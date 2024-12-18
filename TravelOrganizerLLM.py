# Import essential libraries and custom tools
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.openweathermap import OpenWeatherMapQueryRun
from typing import Annotated
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from collections import defaultdict
import re
from datetime import date
from MyAmadeusFlightSearchTool import MyAmadeusFlightSearchTool
from MyAmadeusHotelSearch import MyAmadeusHotelSearchTool

# Loading the environment variables
load_dotenv()

# Loading tools
toolWeather = OpenWeatherMapQueryRun()
toolHotel = MyAmadeusHotelSearchTool(client=MyAmadeusHotelSearchTool.getClient())
toolAmadeus = MyAmadeusFlightSearchTool(client=MyAmadeusFlightSearchTool.getClient())
toolTavily = TavilySearchResults(max_results=2)

# setting all the tools in an array
tools = [toolAmadeus, toolWeather, toolTavily, toolHotel]

# creating the State class that contains messages and the State Graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# Creating the LLM with tools
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

print(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

memory = MemorySaver()

def format_weather_to_json(input_string):
    # Convert weather forecast string to structured JSON format
    weather_data = defaultdict(list)

    # Regex to extract city and state
    city_state_pattern = r"Weather forecast for ([^,]+),([A-Za-z]{2}):"
    city_state_match = re.search(city_state_pattern, input_string)

    if city_state_match:
        city = city_state_match.group(1)
        country = city_state_match.group(2)
    else:
        return {"error": "City and country not found in input"}

    # Regex to extract weather data
    weather_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}):\s*Temperature: ([\d.]+)°C \(min: ([\d.]+)°C, max: ([\d.]+)°C\)\s*Weather: ([^\\n]+)\s*Wind: ([\d.]+) m/s at (\d+)°\s*Humidity: (\d+)%"
    matches = re.findall(weather_pattern, input_string)

    # For each match, group the data by date
    for match in matches:
        date_time = match[0]
        temperature = match[1]
        min_temp = match[2]
        max_temp = match[3]
        weather = match[4]
        wind_speed = match[5]
        wind_direction = match[6]
        humidity = match[7]

        # Extract only the date (without time)
        date = date_time.split(" ")[0]

        weather_data[date].append({
            "time": date_time,
            "temperature": float(temperature),
            "min_temperature": float(min_temp),
            "max_temperature": float(max_temp),
            "weather": weather,
            "wind": {
                "speed": float(wind_speed),
                "direction": int(wind_direction)
            },
            "humidity": int(humidity)
        })

    # Create the final JSON
    result = {
        "city": city,
        "country": country,
        "forecast": []
    }

    # Sort dates and add grouped data
    for date in sorted(weather_data.keys()):
        result["forecast"].append({
            "date": date,
            "data": weather_data[date]
        })

    return result


tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)


def route_tools(
        state: State,
):
    """
    Routes the conversation flow:
    - To tools if the AI message requires tool usage
    - To END if no tools are needed
    """
    if isinstance(state, list):
        ai_message = state[-1]
        print(f"122 a 125 > (state) {state}")
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
        print(f"\n\n(messages) {messages} ")
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    print(f"130> AI_MESSAGE: {ai_message}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


# The tools_condition function returns "tools" if the chatbot asks to use a tool, and "END" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "1"}}


def stream_graph_updates(user_input: str):
    res = ""
    for event in graph.stream({"messages": [("user", user_input)]}, config):
        for value in event.values():
            try:
                print("Assistant:", value["messages"][-1].content)
                res = value["messages"][-1].content
            except Exception as e:
                print(e)
    return res


def askLLM(user_input):
    # Main function to process user queries with date context
    oggi = date.today()

    fixInput = f"{user_input}.Considerando che oggi è {oggi} calcola il periodo esatto."
    res = ""
    try:
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")

        res = stream_graph_updates(fixInput)
    except Exception as e:
        print(e)
        res = e
        # fallback if input() is not available
    return res

def askLLMPriority(input):
    # Categorizes travel requests based on urgency:
    # 0: Travel within 5 days
    # 1: Travel beyond 5 days
    # 2: Not travel-related
    cond = 0

    oggi = date.today()
    # ask = f"{testo}.Considerando che oggi è {oggi} calcola il periodo esatto.\nInserisci anche i codici dei voli trovati e i link ai siti per acquistare i biglietti. Dimmi anche come sarà il meteo in quel periodo. Fammi un breve itinerario e cerca gli eventi e notizie più importanti sulla destinazione nel periodo del viaggio\nformatta il risultato per il markdown di messaggi telegram mettendo frasi e parole tra * o tra _ e per dare più enfasi aggiungi qualche emoji"

    t = f"""Considera che oggi è {oggi} nella seguente frase \"{input}\" si sta cercando di organizzare un viaggio/volo.
        \nRispondimi con un solo numero in base a questa tabella:
        \n0 - è un viaggio/volo che si vuole fare entro 5 giorni da oggi;
        \n1 - non è un viaggio/volo che si vuole fare entro 5 giorni da oggi;
        \n2 - non sta parlando di viaggi"""
    ResType = askLLM(t)
    res = ""
    if "0" in ResType:
        newAsk = f"{input}.Considerando che oggi è {oggi} calcola il periodo esatto.\nInserisci anche i codici dei voli trovati e i link ai corrispondenti  della compagnia corrispondente per acquistare i biglietti. Dimmi anche come sarà il meteo in quel periodo"
        res = askLLM(newAsk)
    elif "1" in ResType:
        newAsk = f"{input}.Considerando che oggi è {oggi} calcola il periodo esatto.\nInserisci anche i codici dei voli trovati e i link ai corrispondenti  della compagnia corrispondente per acquistare i biglietti. Dimmi anche come sarà il meteo in quel periodo. Fammi un breve itinerario e cerca gli eventi e notizie più importanti sulla destinazione nel periodo del viaggio\nformatta il risultato per il markdown di messaggi telegram mettendo frasi e parole tra * o tra _ e per dare più enfasi aggiungi qualche emoji"
        res = askLLM(newAsk)
    else:
        res = f"""Scusa non ho capito.
        \nSono un AI agente di viaggi. Cerca un volo per un determinato periodo"""
    return res


