To remove all the added Backlink sections:

`perl -0 -i -pe 's/---\n### Backlinks[\s\S]*bear:\/\/x-callback-url.*//gim' test_original2.md`
`perl -0 -i -pe 's/---\n### Backlinks[\s\S]*bear:\/\/x-callback-url.*/YOUR NEW CONTENT HERE/gim' test_original2.md`
