import { ApifyClient } from 'apify-client';
import readline from 'readline';
import { GoogleGenAI } from "@google/genai";
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';

//dotenv.config();
dotenv.config({ path: path.resolve('../.env') });

const app = express();
app.use(cors());
app.use(express.json());

// Initialize the ApifyClient with API token
const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});


const ai = new GoogleGenAI({apiKey: process.env.GOOGLE_API_KEY });

const getActivityFromProduct = async (product) => {
  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
        contents: [
      {
        role: "user",
        parts: [
          { text: "You are a specialized translator for a Moroccan store locator. Your task is to convert a product name into the most relevant business category in French (since Google Maps Morocco works best with French/Arabic terms).Translate the user's product into a JSON array of the 3 most relevant business categories in Morocco (in French). Respond only with the JSON array.\nSort by relevance: The first category must be the most populair and common place to find the item.(for example: por fromage il faut meiux commencer par épicerie ou supermaché au lieu de fromagerie).\nVariable length: Provide between 1 and 3 categories depending on where the item is typically sold.\nExamples:\nInput: 'Lait' -> Output: [\"Supermarché\", \"Épicerie\", \"Laiterie\"]\nInput: 'T-shirt' -> Output: [\"Magasin de vêtements\", \"Centre commercial\", \"Friperie\"]\nInput: 'Vis' -> Output: [\"Quincaillerie\", \"Magasin de bricolage\"]\"\n" },
          { text: product },
        ]
    }]
  });
    console.log(response.text);
    const translatedCategories = JSON.parse(response.text);
    return translatedCategories;
    
};

const getPrice = async (product) => {
  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
        contents: [
      {
        role: "user",
        parts: [
            {
            text:
                `Donne une estimation réaliste et actuelle du prix au Maroc (en MAD) pour : ${product}.
                Réponds en 3 à 5 phrases maximum.
                Inclue :
                - une fourchette de prix (min-avg-max)
                - un court contexte (facteurs de variation : marque, qualité, magasin, etc.)
                - un ton neutre et informatif
                Ne pose pas de questions et n'ajoute pas de texte inutile.`
            }
        ]
    }]
  });
    console.log(response.text);
    return response.text;
}

// const PriceInput = ({product}) => {
//   return {
//     "aiModeSearch": {
//         "enableAiMode": true
//     },
//     "chatGptSearch": {
//         "enableChatGpt": false
//     },
//     "disableGoogleSearchResults": true,
//     "focusOnPaidAds": false,
//     "forceExactMatch": false,
//     "includeIcons": false,
//     "includeUnfilteredResults": false,
//     "maxPagesPerQuery": 1,
//     "maximumLeadsEnrichmentRecords": 0,
//     "mobileResults": false,
//     "perplexitySearch": {
//         "enablePerplexity": false,
//         "returnImages": false,
//         "returnRelatedQuestions": false
//     },
//     "queries": `Donne une estimation du prix au Maroc (en MAD) pour: ${product}. Réponds uniquement au format JSON: {"min": nombre, "max": nombre, "moyen": nombre, "unite": "kg/litre/unite"}`,
//     "resultsPerPage": 3,
//     "saveHtml": false,
//     "saveHtmlToKeyValueStore": true
//   }
// }

const formatApifyInput = ({ lat, lng, activity, maxLocals }) => {
    return {
        "includeWebResults": false,
        "language": "en",
        "lat" : parseFloat(lat),
        "lng" : parseFloat(lng),
        "countryCode" : "ma",
        "zoom" : 20,
        "maxCrawledPlacesPerSearch": maxLocals,
        "maxImages": 0,
        "maximumLeadsEnrichmentRecords": 0,
        "scrapeContacts": false,
        "scrapeDirectories": false,
        "scrapeImageAuthors": false,
        "scrapePlaceDetailPage": false,
        "scrapeReviewsPersonalData": true,
        "scrapeSocialMediaProfiles": {
            "facebooks": false,
            "instagrams": false,
            "tiktoks": false,
            "twitters": false,
            "youtubes": false
        },
        "scrapeTableReservationProvider": false,
        "searchStringsArray": activity,
        "skipClosedPlaces": false        
    }
};



app.post('/api/search-places', async(req, res) => {
    try{
        const { product, latitude, longitude, maxResults = 1 } = req.body;

        // Validation des entrées
        if (!product || !latitude || !longitude) {
            return res.status(400).json({ 
                error: 'Missing required fields: product, latitude, longitude' 
            });
        }

        //const actorPriceInput = PriceInput({product: product});
        const priceResult = await getPrice(product);
        console.log("Price generated : ",priceResult);

        //const priceRun = await client.actor("nFJndFXA5zjCTuudP").call(actorPriceInput);

        // const { items: priceData } = await client.dataset(priceRun.defaultDatasetId).listItems();
        // console.log("Product Price :", priceData);

        const translatedCategories = await getActivityFromProduct(product);
        console.log(`Translated categories for '${product}':`, translatedCategories);

        // Préparer l'entrée pour l'Actor
        //const actorInput = inp(userInputs);
        const actorInput = formatApifyInput({
            lat: latitude,
            lng: longitude,
            activity: translatedCategories,
            maxLocals: maxResults      
        });

        const run = await client.actor("nwua9Gu5YrADL7ZDj").call(actorInput);
        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        console.log(items);

        const places = items.map(item => ({
            id: item.placeId,
            name: item.title,
            address: item.address,
            latitude: item.location["lat"],
            longitude: item.location["lng"],
            phone: item.phone,
            website: item.website,
            categories: item.categories,
            url: item.url,
            distance: calculateDistance(latitude, longitude, item.lat, item.lng)
        }));

        places.sort((a, b) => a.distance - b.distance);

        res.json({
            success: true,
            product: product,
            categories: translatedCategories,
            total: places.length,
            places: places,
            priceInfo: priceResult
        });

        }
        catch(error){
            console.error('Error:', error);
            res.status(500).json({ 
                success: false, 
                error: error.message 
            });
        }
});

// Calcul de distance (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Rayon de la Terre en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Fonction pour exécuter l'Actor et récupérer les résultats
const fetchActorResults = async (inp) => {
    const run = await client.actor("nwua9Gu5YrADL7ZDj").call(inp);
    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    return items;
};


app.listen(3000, () => {
    console.log(`Server running on port 3000`);
});

