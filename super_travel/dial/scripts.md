# AGENT FINDS NEARBY CARRIERS

curl -s https://api.openai.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-5.4",
    "tools": [{"type": "web_search"}],
    "input": "Find 10 travel insurance providers in Barcelona, Spain. Include local insurance brokers and agencies offering travel insurance. Search English, Spanish, and Catalan sources. Return a table with company name, address, phone number, website, and services. Prioritize physical offices in Barcelona. Do not invent contact details. Cite sources."
  }' | jq -r '.output[] | select(.type=="message") | .content[] | select(.type=="output_text") | .text'


  # AGENT USES DIAL TO CALL VARIOUS PROVIDERS FOR EACH NUMBER 


  dial call \
  --to +16103950526 \
  --outbound-instruction "Call this insurance provider with [PAYLOAD INFORMATION] and receive a quote for the desired plan" \
  --language en-US \
  --from-number-id cmv4czstp00vw0foxem21fcai

  # INFORMATION IS SENT TO OPERATOR DASHBOARD FOR APPROVAL IF NEEDED

