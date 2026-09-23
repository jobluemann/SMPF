import requests

payload = {
    "platforms": ["x"],
    "content": {
        "text": "I generate 100% of my own electricity. Zero from Eskom.\n\nANC still bills me 'connection fees' + property rates + municipal charges.\n\nFor WHAT? Crater roads? Brown water? 67% of municipalities bankrupt?\n\nLegalized extortion, plain and simple.\n\n#TaxationIsTheft #ANC #SouthAfrica #Libertarian #Conservative"
    }
}

r = requests.post(
    "https://soccer-man-dramatically-save.trycloudflare.com/api/post",
    headers={"Content-Type": "application/json"},
    json=payload
)
print("Status:", r.status_code)
print("Response:", r.text)
