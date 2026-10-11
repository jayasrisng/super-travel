"""Wardrobe, voting and per-trip packing. Transactions are owned by Notebook routes."""

import base64
import io
from datetime import date, timedelta
from uuid import NAMESPACE_URL, uuid4, uuid5

from PIL import Image, UnidentifiedImageError

from super_travel.consumer.models import (
    Outfit,
    OutfitVote,
    PackingItem,
    PackingSummary,
    WardrobeItem,
)
from super_travel.consumer.seed import COLORS
from super_travel.control.store import ControlError


class WardrobeService:
    def wardrobe(self, actor):
        self.initialize(actor)
        return [WardrobeItem(**item) for item in self.collection(actor, "wardrobe")]

    def add_clothing(self, actor, payload):
        self.initialize(actor)
        item = WardrobeItem(**payload.model_dump(), id=uuid4())
        if not item.image:
            item.image = (
                f"/wardrobe/{item.category}-cream.svg"
                if item.category != "essentials"
                else "/wardrobe/accessories-cream.svg"
            )
        if item.image not in {
            f"/wardrobe/{category}-{color}.svg"
            for category in ("tops", "bottoms", "shoes", "accessories")
            for color in COLORS
        }:
            raise ControlError(
                422, "invalid_image", "Upload photos through the photo endpoint"
            )
        return self.put(actor, "wardrobe", item)

    def update_clothing(self, actor, identifier, payload, etag):
        item = self.owned(actor, "wardrobe", identifier)
        self.version(item, etag)
        if payload.image != item["image"]:
            raise ControlError(
                422, "invalid_image", "Use photo upload to replace images"
            )
        return self.put(
            actor,
            "wardrobe",
            WardrobeItem(
                **{**item, **payload.model_dump(), "version": item["version"] + 1}
            ),
        )

    def photo(self, actor, identifier, content, mime, etag):
        item = self.owned(actor, "wardrobe", identifier)
        self.version(item, etag)
        try:
            raw = base64.b64decode(content, validate=True)
            if len(raw) > 2_000_000:
                raise ValueError("Too large")
            with Image.open(io.BytesIO(raw)) as image:
                if (
                    image.format not in ("JPEG", "PNG", "WEBP")
                    or image.width * image.height > 12_000_000
                ):
                    raise ValueError("Unsupported image")
                image.thumbnail((1000, 1000))
                clean = image.convert("RGB")
                output = io.BytesIO()
                clean.save(output, "JPEG", quality=85)
        except (
            ValueError,
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
        ) as exc:
            raise ControlError(
                422, "invalid_photo", "Use a JPEG, PNG or WebP photo under 2 MB"
            ) from exc
        identity = str(uuid4())
        self.put(
            actor,
            "media",
            {
                "id": identity,
                "mime": "image/jpeg",
                "content": base64.b64encode(output.getvalue()).decode(),
            },
        )
        if item["image_mode"] == "uploaded":
            self.store.db.execute(
                "DELETE FROM objects WHERE id=? AND actor=? AND kind=?",
                (item["image"].split("/")[-1], str(actor), "media"),
            )
        item.update(
            image=f"/v1/consumer/media/{identity}",
            image_mode="uploaded",
            version=item["version"] + 1,
        )
        return self.put(actor, "wardrobe", item)

    def outfits(self, actor, request):
        self.initialize(actor)
        trip = self.owned(actor, "trip", request.trip_id) if request.trip_id else None
        clothing = self.collection(actor, "wardrobe")
        trip_availability = (
            {
                item["wardrobe_item_id"]: item["availability"]
                for item in self.collection(actor, "packing", request.trip_id)
            }
            if request.trip_id
            else {}
        )
        groups = {
            key: [
                item
                for item in clothing
                if item["category"] == key
                and item["availability"] == "ready"
                and trip_availability.get(item["id"], "ready") == "ready"
                and request.occasion in item["occasions"]
            ]
            for key in ("tops", "bottoms", "shoes", "accessories")
        }
        if any(not group for group in groups.values()):
            return []
        votes = {v["outfit_id"]: v["decision"] for v in self.collection(actor, "vote")}
        liked_items = {
            identifier
            for outfit in self.collection(actor, "outfit")
            if votes.get(outfit["id"]) == "like"
            for identifier in outfit["item_ids"]
        }
        dates = (
            [
                date.fromisoformat(trip["start_date"]) + timedelta(days=i)
                for i in range(
                    min(
                        61,
                        (
                            date.fromisoformat(trip["end_date"])
                            - date.fromisoformat(trip["start_date"])
                        ).days
                        + 1,
                    )
                )
            ]
            if trip and trip["start_date"] and trip["end_date"]
            else []
        )
        existing = self.collection(actor, "outfit")
        generated = []
        for i in range(min(30, len(groups["tops"]) * len(groups["bottoms"]))):
            choices = [
                groups["tops"][i % len(groups["tops"])],
                groups["bottoms"][
                    (i // len(groups["tops"]) + i + 1) % len(groups["bottoms"])
                ],
                groups["shoes"][i % len(groups["shoes"])],
                groups["accessories"][(i + 2) % len(groups["accessories"])],
            ]
            if request.temperature_c < 12 and choices[0]["warmth"] < 3:
                continue
            identity = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{actor}:{request.trip_id}:{request.occasion}:"
                    + ":".join(item["id"] for item in choices),
                )
            )
            if votes.get(identity) == "dislike":
                continue
            score = sum(
                (3 if item["favorite"] else 0) + (2 if item["id"] in liked_items else 0)
                for item in choices
            )
            # Neutral capsule colours pair consistently; accents count at most once.
            accents = sum(
                item["color"] in ("clay", "sage", "blue") for item in choices[:2]
            )
            if accents > 1:
                continue
            outfit = Outfit(
                id=identity,
                trip_id=request.trip_id,
                item_ids=[item["id"] for item in choices],
                title=f"{choices[0]['color'].title()} & {choices[1]['color']}",
                occasion=request.occasion,
                suitable_days=dates,
                explanation=f"Coordinated capsule layers for {request.occasion}; comfortable shoes. {request.temperature_c}°C is {request.weather_mode} input, not a live forecast.",
                score=score,
                weather_mode=request.weather_mode,
                temperature_c=request.temperature_c,
            )
            old = next((value for value in existing if value["id"] == identity), None)
            if old:
                outfit.version = old["version"] + 1
            self.put(actor, "outfit", outfit)
            generated.append(outfit)
        return sorted(
            generated, key=lambda item: (-item.score, item.title, str(item.id))
        )

    def vote(self, actor, identifier, decision):
        outfit = self.owned(actor, "outfit", identifier)
        old = next(
            (
                v
                for v in self.collection(actor, "vote")
                if v["outfit_id"] == str(identifier)
            ),
            None,
        )
        # Keep previous value for true undo, including a changed like/dislike.
        if old:
            old["previous_decision"] = old["decision"]
            old.update(
                decision=decision,
                version=old["version"] + 1,
                created_at=self.store.now().isoformat(),
            )
            return self.put(actor, "vote", old)
        return self.put(
            actor,
            "vote",
            OutfitVote(
                id=uuid4(),
                outfit_id=identifier,
                trip_id=outfit["trip_id"],
                decision=decision,
                created_at=self.store.now(),
            ),
        )

    def undo_vote(self, actor, identifier):
        vote = next(
            (
                v
                for v in self.collection(actor, "vote")
                if v["outfit_id"] == str(identifier)
            ),
            None,
        )
        if not vote:
            raise ControlError(404, "not_found", "Vote not found")
        if vote.get("previous_decision"):
            vote.update(
                decision=vote.pop("previous_decision"), version=vote["version"] + 1
            )
            self.put(actor, "vote", vote)
        else:
            self.store.db.execute(
                "DELETE FROM objects WHERE id=? AND actor=?", (vote["id"], str(actor))
            )

    def packing(self, actor, trip_id, build=False):
        self.owned(actor, "trip", trip_id)
        likes = {
            vote["outfit_id"]
            for vote in self.collection(actor, "vote", trip_id)
            if vote["decision"] == "like"
        }
        outfits = [
            Outfit(**item)
            for item in self.collection(actor, "outfit", trip_id)
            if item["id"] in likes
        ]
        wardrobe = {item["id"]: item for item in self.collection(actor, "wardrobe")}
        old = {
            item["wardrobe_item_id"]: item
            for item in self.collection(actor, "packing", trip_id)
        }
        needed = []
        if build:
            usages = {
                identifier: []
                for identifier, previous in old.items()
                if previous.get("manual")
            }
            for outfit in outfits:
                for identifier in outfit.item_ids:
                    usages.setdefault(str(identifier), []).append(outfit)
            for identifier, uses in usages.items():
                item = wardrobe.get(identifier)
                if item is None:
                    needed.append("Removed clothing item; select a substitution")
                    continue
                previous = old.get(identifier)
                packing = PackingItem(
                    id=previous["id"] if previous else uuid4(),
                    trip_id=trip_id,
                    wardrobe_item_id=identifier,
                    name=item["name"],
                    image=item["image"],
                    category=item["category"],
                    packed=previous["packed"] if previous else False,
                    manual=previous.get("manual", False) if previous else False,
                    outfit_ids=[outfit.id for outfit in uses],
                    relevant_days=sorted(
                        {day for outfit in uses for day in outfit.suitable_days}
                    ),
                    availability=previous["availability"]
                    if previous
                    else item["availability"],
                    version=previous["version"] + 1 if previous else 1,
                )
                self.put(actor, "packing", packing)
            for identifier, previous in old.items():
                if identifier not in usages:
                    self.store.db.execute(
                        "DELETE FROM objects WHERE id=? AND actor=?",
                        (previous["id"], str(actor)),
                    )
        items = self.collection(actor, "packing", trip_id)
        for item in items:
            clothing = wardrobe.get(item["wardrobe_item_id"])
            if clothing is None:
                item["availability"] = "unavailable"
                needed.append("Removed item; choose a substitute for " + item["name"])
            if clothing:
                item.update(
                    name=clothing["name"],
                    image=clothing["image"],
                    category=clothing["category"],
                )
                if clothing["availability"] != "ready":
                    item["availability"] = clothing["availability"]
            if clothing and clothing["ownership_status"] == "needed":
                needed.append(clothing["name"])
        return PackingSummary(
            items=items,
            unique_items=len(items),
            liked_outfits=outfits,
            needed_items=needed,
            substitutions=[
                "Choose a ready item from the same category for anything dirty, unavailable or missing."
            ]
            if needed or any(item["availability"] != "ready" for item in items)
            else [],
        )

    def add_packing(self, actor, trip_id, item_id):
        self.owned(actor, "trip", trip_id)
        wardrobe = self.owned(actor, "wardrobe", item_id)
        old = next(
            (
                item
                for item in self.collection(actor, "packing", trip_id)
                if item["wardrobe_item_id"] == str(item_id)
            ),
            None,
        )
        if old:
            old.update(manual=True, version=old["version"] + 1)
            return self.put(actor, "packing", old)
        return self.put(
            actor,
            "packing",
            PackingItem(
                id=uuid4(),
                trip_id=trip_id,
                wardrobe_item_id=item_id,
                name=wardrobe["name"],
                category=wardrobe["category"],
                image=wardrobe["image"],
                manual=True,
                outfit_ids=[],
                relevant_days=[],
                availability=wardrobe["availability"],
            ),
        )
