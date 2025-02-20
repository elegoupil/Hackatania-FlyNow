import random
from langchain_community.tools.amadeus.base import AmadeusBaseTool
from pydantic import BaseModel, Field
from typing import Type
from amadeus import Client

class MyAmadeusHotelSearchTool(AmadeusBaseTool):
    class HotelSearchSchema(BaseModel):
        # Parametri per la ricerca degli hotel
        city_code: str = Field(description="IATA city code where the user wants to search for hotels (e.g., NYC for New York, LON for London).")
        check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format.")
        check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format.")
        adults: int = Field(default=1, description="Number of adults for the hotel booking.")
        max_hotels: int = Field(default=2, description="Maximum number of hotel offers to return.")

    name: str = "hotel_search"
    description: str = "Search for hotel offers in a specific city."
    args_schema: Type[BaseModel] = HotelSearchSchema

    def _run(self, city_code: str, check_in_date: str, check_out_date: str, adults: int = 1, max_hotels: int = 2):
        # Usa il client Amadeus per cercare offerte di hotel
        client = self.client  # Automatically configured by AmadeusBaseTool
        try:
            # Called to the endpoint hotel_offers_search
            ListHotel = client.reference_data.locations.hotels.by_city.get(
                cityCode = city_code
            )
            print(f"Lista Hotel a {city_code}: {ListHotel.data}")
            hotelID = ListHotel.data[0]
            hotel_ids = []

            #  Iterate on the hotels and add the hotelId to the list
            i = 0
            totHotel = len(ListHotel.data)

            print(f"\n\nTot Hotel: {totHotel}\n\n")
            for i in range (0,10):
                hotel_ids.append(ListHotel.data[random.randint(0,totHotel-1)]['hotelId'])
            # for hotel in ListHotel.data:
            #     #hotel_ids.append(hotel['hotelId'])
            #     ch = random.randint(0,totHotel-1)%10
            #     if 0 == ch%i:
            #         hotel_ids.append(hotel['hotelId'])
            #         i+=1

            #     if i == 10:
            #         break  # Assure that 'hotelId' is the correct name of the attribute
            print(hotel_ids)
            print(f"Hotel0: {hotel_ids[0]}")
            response = client.shopping.hotel_offers_search.get(
                hotelIds = hotel_ids,
                cityCode=city_code,               # Usa il codice della città
                checkInDate=check_in_date,        # Data di check-in
                checkOutDate=check_out_date,      # Data di check-out
                adults=adults,                    # Numero di adulti
                roomQuantity=1,                   # Numero di stanze
                currency="USD",                   # Valuta
                sort="PRICE"                       # Ordinamento per prezzo
            )
            print(f"Response: {response}")
            return response.data
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Data: {response.data}")

            # Check if the answer is correct
            if response.status_code != 200:
                return {"error": f"API returned status code {response.status_code}"}
        
            # Elabora la risposta per restituire solo un numero limitato di hotel
            hotels = response.data[:max_hotels]  # Limita il numero di hotel
            results = []

            for hotel in hotels:
                # Prepara i dettagli dell'hotel
                hotel_info = {
                    "hotel_name": hotel["hotel"]["name"],
                    "city": hotel["hotel"]["address"]["cityName"],
                    "check_in": hotel["offers"][0]["checkInDate"],
                    "check_out": hotel["offers"][0]["checkOutDate"],
                    "price": hotel["offers"][0]["price"]["total"],
                    "currency": hotel["offers"][0]["price"]["currency"],
                    "room_description": hotel["offers"][0].get("room", {}).get("description", {}).get("text", "N/A"),
                }
                results.append(hotel_info)

            return results

        except Exception as e:
            # Error Management
            
            return {"error": str(e)}

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported yet.")


    @staticmethod
    def getClient():
        # Loading the environment variables
        load_dotenv()
        
        # Configura il client Amadeus con le credenziali
        amadeus_client = Client(
            client_id="GPBeOGYq15rpYAKlJi8nG0e4DLUcvMrk",  # Sostituisci con il tuo client_id
            client_secret="3ETaMtYhnfczzUcW"              # Sostituisci con il tuo client_secret
        )
        return amadeus_client
