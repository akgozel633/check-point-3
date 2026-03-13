-- Table: recipes
CREATE TABLE recipes (
id TEXT PRIMARY KEY,
name TEXT NOT NULL,
category TEXT NOT NULL,
rating INTEGER NOT NULL,
image_url TEXT,
ingredients TEXT NOT NULL,
instructions TEXT NOT NULL,
favorite INTEGER NOT NULL DEFAULT 0
);
-- Example row:
INSERT INTO recipes VALUES (
'a73b7d5d-1395-4119-ab36-bed68372b937',
'fsefse',
'Breakfast',
5,
'https://tse1.mm.bing.net/th/id/OIP.MRirTpv0Ts5S_yxL2Y3U7gHaHa?rs=1&pid=ImgDetMain&o=7&rm=3',
'daswd',
'awdawd',
0
);