"""Render Twitter Friends Map"""
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


def stream_template(template_name, **context):
    """Stream a template's content gradually.

    Used for updating a page step by step and not all at once.
    :param template_name: name of the template file.
    :param context: dynamic content to update
    :return: a stream object
    """
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv


def get_friends(name: str, fg):
    """Get location and friends of a user.

    Add location to the FeatureGroup.
    :param name: name from the form
    :param fg: FeatureGroup object
    :return: (list of friends, a tuple of coordinates)
    """
    try:
        name = "@" + name
        user = api.GetUser(screen_name=name)
    except TwitterError:
        print("This user doesn't exist. Try again!")
        return None, None
    location = user.location
    if location:
        location = locator.geocode(query=location, language="en")
        if location:
            location = (location.latitude, location.longitude)
            sec_source = "static/id-card-solid.svg"
            if user.profile_image_url:
                main_source = user.profile_image_url
            else:
                main_source = sec_source
            fg.add_child(folium.Marker(
                location=location,
                popup='<img src="{}" alt="{}"><i>'.format(main_source,
                                                          sec_source) +
                      user.name + '</i>',
                icon=folium.Icon(prefix="fa",
                                 icon="twitter-square",
                                 color="blue",
                                 icon_color="red")
            ))
    else:
        location = (0, 0)

    return api.GetFriends(screen_name=name), location


@app.route("/", methods=["GET", "POST"])
def build_map():
    """Generate web pages and dynamically build a map.

    Using return from the web form dynamically generate a loading page
    (with stream instead of render). When all its content is streamed,
    generate a button for the web map.
    :return: one of web pages: form, loading (render and stream objects)
    """
    if flask.request.method == "GET":
        return flask.render_template("form.html", error=False)

    friends_group = folium.FeatureGroup(name="Friends map")
    name = flask.request.form.get("name")
    if not re.fullmatch("[\\w_]{}".format({len(name)}), name):
        return flask.render_template("form.html", error=True)
    else:
        friends, location = get_friends(name, friends_group)

    if friends is None:
        return flask.render_template("form.html", error=True)

    def generate_map(friends, location, fg):
        """Generate the map and dynamically add to the loading page.

        :param friends: a list of friends of the user
        :param location: the location of the user
        :param fg: FeatureGroup object
        :return: a tuple of username and boolean value for the loading page
        """
        friends_map = folium.Map(location=location, zoom_start=5)
        all_coords = {location}
        mode_x, mode_y = 0.005, -0.005

        for i, friend in enumerate(friends):
            friend = api.GetUser(screen_name=friend.screen_name)
            location = friend.location
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
                    coords = (coords[0] +
                              random.triangular(-0.01, 0.01, mode_x),
                              coords[1] +
                              random.triangular(-0.01, 0.01, mode_x))
                    mode_x *= random.choice([-1, 1])
                    mode_y *= random.choice([-1, 1])
                    all_coords.add(coords)
                sec_source = "static/id-card-solid.svg"
                if friend.profile_image_url:
                    main_source = friend.profile_image_url
                else:
                    main_source = sec_source
                fg.add_child(
                    folium.Marker(
                        location=coords,
                        icon=folium.Icon(prefix="fa",
                                         icon="twitter",
                                         color="cadetblue",
                                         icon_color="orange"),
                        popup='<img src="{}" alt="{}"><i>'.format(main_source,
                                                                  sec_source) +
                              friend.name + '</i>',
                        tooltip="Click to see friend!"
                    )
                )
            if i == len(friends) - 1:
                friends_map.add_child(fg)
                friends_map.save("templates/friends_map.html")
                yield (friend.name, True)
            else:
                yield (friend.name, False)

    friends_list = generate_map(friends, location, friends_group)

    return flask.Response(flask.stream_with_context(
        stream_template("loading_page.html", friends=friends_list)
    ))


@app.route("/twitter_friends_map", methods=["POST"])
def show_map():
    """Render the map.

    :return: render object of the map
    """
    return flask.render_template("friends_map.html")


if __name__ == "__main__":
    app.run(debug=True)
