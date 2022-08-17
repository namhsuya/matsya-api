from fastapi import FastAPI, Depends
from pydantic import create_model
from fastapi.responses import StreamingResponse
import io
import pandas as pd


app = FastAPI()

# Query arguments
query_params = {
    "initial_weight": (float, 25),
    "final_weight": (float, 1000),
    "duration": (int, 360),
    "feed_multiplier": (float, 1.4),
    "fish_qty": (float, 7000),
    "feed_cost_per_kg": (float, 3),
    "get_csv": (bool, False)
}

query_model = create_model("Query", **query_params)

@app.get("/")
def evaluate(params: query_model = Depends()):
    params_as_dict = params.dict()

    initial_weight=params_as_dict['initial_weight']
    final_weight=params_as_dict['final_weight']
    duration=params_as_dict['duration']
    feed_multiplier=params_as_dict['feed_multiplier']
    fish_qty=params_as_dict['fish_qty']
    feed_cost_per_kg=params_as_dict['feed_cost_per_kg']
    get_csv=params_as_dict['get_csv']

    result = matsya(initial_weight, final_weight, duration, feed_multiplier, fish_qty, feed_cost_per_kg, get_csv)
    if get_csv:
        stream = io.StringIO()
        result.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=matsya.csv"
        return response
    else:
        return {"result": f"Total feed cost for {fish_qty} fishes = Rs {result}"}

def matsya(initial_weight, final_weight, duration, feed_multiplier, fish_qty, feed_cost_per_kg, get_csv):
    
    growth_rate = (final_weight - initial_weight) / duration

    feed_sum = initial_weight
    feed=[feed_sum]

    for _ in range(duration):
        feed_sum = feed_sum + growth_rate
        feed.append(feed_sum)

    feed = pd.Series(feed)
    df = pd.DataFrame(feed, columns=["per_day_per_fish_weight"])
    df["per_day_per_fish_feed_weight"] = [ (x*feed_multiplier) for x in df.per_day_per_fish_weight ]
    
    # print(f"Total feed cost for {fish_qty} fishes = Rs {total_feed_cost}")
    feed_weight_per_fish = df.per_day_per_fish_weight.sum() / 1000
    total_feed_weight = feed_weight_per_fish * fish_qty
    total_feed_cost = total_feed_weight * feed_cost_per_kg

    if get_csv:
        return df
    else:
        return total_feed_cost
    