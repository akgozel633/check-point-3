# Current Data Structure
## Teacher for fun check image url adress in first block of json
Current data format (JSON file: recipes.json):
[
  {
        "id": "a73b7d5d-1395-4119-ab36-bed68372b937",
        "name": "fsefse",
        "category": "Breakfast",
        "rating": 5,
        "image_url": "https://tse1.mm.bing.net/th/id/OIP.MRirTpv0Ts5S_yxL2Y3U7gHaHa?rs=1&pid=ImgDetMain&o=7&rm=3",
        "ingredients": "daswd",
        "instructions": "awdawd",
        "favorite": false
    }
]

This is an array of recipe objects. Each recipe has:
 id: Unique string 
 name: String 
 category: String 
 rating: Integer 
 image_url: String (URL or empty)
 ingredients: String 
 instructions: String
 favorite: Boolean (true/false)