"""Twitter Map Renderer for pythonanywhere.com"""
from app_tokens import *
import twitter
from twitter.error import TwitterError
import re
import geopy
from geopy.exc import GeocoderTimedOut
import folium
import random
import flask


app = flask.Flask(__name__)
locator = geopy.Nominatim(user_agent="Alex-Quickcoder", timeout=5)
api = twitter.Api(consumer_key=CONSUMER_KEY,
                  consumer_secret=CONSUMER_SECRET,
                  access_token_key=ACCESS_KEY,
                  access_token_secret=ACCESS_SECRET)


def generate_map(name, fg):
    """Generate map and return it.

    :param name: name of the user
    :param fg: FeatureGroup object
    :return: Map object
    """
    try:
        name = "@" + name
        user = api.GetUser(screen_name=name, return_json=True)
    except TwitterError:
        print("This user doesn't exist. Try again!")
        return None, None
    location = user["location"]
    if location:
        location = locator.geocode(query=location, language="en")
        if location:
            location = (location.latitude, location.longitude)
            fg.add_child(folium.Marker(
                location=location,
                popup="<i>" + user["name"] + "</i>",
                icon=folium.Icon(color='red')
            ))
    else:
        location = (0, 0)

    friends = api.GetFriends(screen_name=name)
    if not friends:
        return flask.render_template("form.html", error=True)

    friends_map = folium.Map(location=location, zoom_start=5)
    all_coords = {location}
    mode_x, mode_y = 0.005, -0.005

    for i, friend in enumerate(friends):
        friend = api.GetUser(screen_name=friend.screen_name, return_json=True)
        location = friend["location"]
        if location:
            try:
                location = locator.geocode(query=location, language="en")
            except GeocoderTimedOut:
                location = None
        if location:
            coords = (location.latitude, location.longitude)
            if coords not in all_coords:
                all_coords.add(coords)
            else:
                coords = (coords[0] + random.triangular(-0.01, 0.01, mode_x),
                          coords[1] + random.triangular(-0.01, 0.01, mode_x))
                mode_x *= random.choice([-1, 1])
                mode_y *= random.choice([-1, 1])
                all_coords.add(coords)
            fg.add_child(
                folium.Marker(
                    location=coords,
                    popup="<i>" + friend["name"] + "</i>",
                    tooltip="Click to see friend!"
                )
            )
    friends_map.add_child(fg)
    # friends_map.save("templates/friends_map.html")
    return friends_map


@app.route("/", methods=["GET", "POST"])
def build_map():
    """Generate web pages and dynamically build a map.

    Using return from the web form generate the web map.
    :return: html rendition of the map
    """
    if flask.request.method == "GET":
        return flask.render_template("form.html", error=False)

    name = flask.request.form.get("name")
    if not re.fullmatch("[\\w_]{}".format({len(name)}), name):
        return flask.render_template("form.html", error=True)
    else:
        friends_group = folium.FeatureGroup(name="Friends map")
        fr_map = generate_map(name, friends_group)
        return fr_map._repr_html_()


if __name__ == "__main__":
    app.run(debug=True)
