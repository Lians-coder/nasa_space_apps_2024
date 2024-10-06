from flask import Flask, render_template, redirect, request, flash, Response
from flask_session import Session
from flask_caching import Cache
import random
import os
import io
import json
import math
from astroquery.gaia import Gaia
from astroquery.utils.tap.core import TapPlus
import astropy
import astropy.units as u
import matplotlib.pyplot as plt


config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 30,
    "SESSION_PERMANENT": False,
    "SESSION_TYPE": "filesystem"
}

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config.from_mapping(config)
Session(app)
cache = Cache(app)


@app.route("/", methods=["GET", "POST"])
def index():
    """ Show rendered exosky """
    if request.method == "POST":
        flash("Rendering ExoSky...")
        redirect("/render")
    else:
        # star_data, exo_pl_id = load_preview()
        # tO-DO: render preview from JSON
        return render_template("index.html")


def load_preview():
    """ Load star data from a JSON file """
    # Directory where the files are located
    directory = "/static/assets/preview"
    # List all files in the directory
    files = os.listdir(directory)
    # Filter out any directories or non-file items (optional)
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    # Choose a random file from the list
    random_file = random.choice(files)

    # Open the random file
    with open(os.path.join(directory, random_file), 'r') as file:
        data = json.load(file)
    # Get exoplanet identifier fromfile name
    filename = file.name
    exo_pl_id = os.path.splitext(os.path.basename(filename))[0]

    # Define the keys (metadata names)
    keys = ["designation", "ra", "dec", "b", "l", "grvs_mag", "distance_gspphot"]
    # Extract the star data from the "data" section of the JSON
    star_data = [dict(zip(keys, row)) for row in data["data"]]

    # exo_pl_name = random_file.splitext[0]
    return star_data, exo_pl_id


@app.route("/render", methods=["GET", "POST"])
def render():
    try:
        if request.method == "POST":
            exoplanet_id = request.form.get("exoplanet_id")
            print(exoplanet_id)
            if not exoplanet_id:
                raise ValueError("Exoplanet ID is required.")

            # Run TAP query to fetch data
            p = fetch_exo_pl_data(exoplanet_id)
            planet_name = p[0]["pl_name"]

            # Add nesessary values to run another query
            cube_size = 200
            angle_size = math.degrees(cube_size/p["sy_dist"])
            # Result of a TAP query to fetch stellar data
            stars = fetch_star_data(p["sy_dist"], cube_size, p["glon"], p["glat"], angle_size)

            planet_cartesian = astropy.coordinates.spherical_to_cartesian(p["sy_dist"]*u.parsec,
                                                                        math.radians(p["glat"]),
                                                                        math.radians(p["glon"]))

            theta, radius, area, theta_b, radius_b, area_b = coordinates(stars, planet_cartesian)

            # Making plots
            render_exosky(theta, radius, area, theta_b, radius_b, area_b, planet_name)
            return render_template("rendered.html", method="POST")
        else:
            return render_template("render.html")
    except Exception as e:
        # Log the error for debugging
        print(f"Error: {e}")
        # You might want to return a more user-friendly error message
        return render_template("error.html", error=str(e))


def coordinates(stars, planet_cartesian):
    # Cartesian CO of an exoplanet
    r_cart = []
    # cartesian coordinates of stars for planet (galactical)
    star_cart = []
    # spherical coordinates of stars for planet (galactical)
    star_sph = []

    # Holders for values above galactic plane
    theta = []
    radius = []
    area = []
    # Holders for values below galactic plane
    theta_b = []
    radius_b = []
    area_b = []

    # Populate holders
    for i in range(len(stars)):
        r_cart.append(astropy.coordinates.spherical_to_cartesian([i]['distance_gspphot']*u.parsec,  # distance
                                                                 # latitude
                                                                 math.radians(stars[i]['b']),
                                                                 math.radians(stars[i]['l'])))   # longitude
        # Offset
        star_cart.append([r_cart[i][0] - planet_cartesian[0],
                          r_cart[i][1] - planet_cartesian[1],
                          r_cart[i][2] - planet_cartesian[2]])

        # Transpose to spherical
        star_sph.append(astropy.coordinates.cartesian_to_spherical(star_cart[i][0]*u.parsec,
                                                                   star_cart[i][1]*u.parsec,
                                                                   star_cart[i][2]*u.parsec))

    # Filter bottom stars
    if (star_sph[i][1].value < 0):
        radius_b.append(math.pi / 2 - math.fabs(star_sph[i][1].value))
        theta_b.append(star_sph[i][2].value)
        area_b.append(100*math.pow(10, stars[i][5]/-2.5))
    # Filter upper stars
    else:
        radius.append(math.pi / 2 - star_sph[i][1].value)
        theta.append(star_sph[i][2].value)
        area.append(100 * math.pow(10, stars[i][5] / -2.5))

    return theta, radius, area, theta_b, radius_b, area_b


def render_exosky(theta, radius, area, theta_b, radius_b, area_b, planet_name):
    """ Making plots of exosky """
    plot1(theta, radius, area, planet_name)
    plot2(theta_b, radius_b, area_b, planet_name)

# Route to generate first plot
@app.route('/plot1.png')
def plot1(theta, radius, area, pl_name):

    """ Making plot of exosky """
    fig1 = plt.figure(figsize=[10, 10])
    zenith = fig1.add_subplot(projection='polar')
    c = zenith.scatter(theta, radius, c='b', s=area, alpha=0.75, marker=".")
    c.set_title(pl_name + " exosky")

    # Save plot to in-memory file
    output = io.BytesIO()
    fig1.savefig(output, format='png')
    output.seek(0)

    return Response(output.getvalue(), mimetype='image/png')

# Route to generate second plot
@app.route('/plot1.png')
def plot2(theta, radius, area, pl_name):

    """ Making plot of exosky """
    fig2 = plt.figure(figsize=[10, 10])
    nadir = fig2.add_subplot(projection='polar')
    c = nadir.scatter(theta, radius, c='b', s=area, alpha=0.75, marker=".")
    c.set_title(pl_name + " exosky")

    # Save plot to in-memory file
    output = io.BytesIO()
    fig2.savefig(output, format='png')
    output.seek(0)

    return Response(output.getvalue(), mimetype='image/png')


def fetch_exo_pl_data(exo_pl_id):
    """ A function to execute the TAP query for exoplanet info """

    planet = TapPlus(url="https://exoplanetarchive.ipac.caltech.edu/TAP")
    query = ("""
            SELECT DISTINCT pl_name pl_name,
                            sy_dist,
                            glat,
                            glon,
                            ra,
                            dec
            FROM k2pandc
            WHERE pl_name = ?
            """,
            exo_pl_id
            )

    job = planet.launch_job_async(query)
    results = job.get_results()
    if len(results) == 0:
        raise ValueError("No data returned for the given exoplanet ID")
    p = results[0]
    print(p)
    return p


def fetch_star_data(dist_planet, cube_size, glon_planet, glat_planet, angle_size):
    """ A function to execute the TAP query using Astroquery """
    # ADQL query to retrieve star data
    adql_query = ("""
                SELECT designation, ra, dec, b, l, grvs_mag, distance_gspphot
                    FROM gaiadr3.gaia_source
                    WHERE grvs_mag < 6
                        AND distance_gspphot BETWEEN ? AND ?
                        AND l BETWEEN ? AND ?
                        AND b BETWEEN ? AND ?
                """,
                dist_planet - cube_size, dist_planet + cube_size,
                glon_planet - angle_size, glon_planet + angle_size,
                glat_planet - angle_size, glat_planet + angle_size)
    # Execute the TAP query
    job = Gaia.launch_job(adql_query)
    result = job.get_results()

    # Convert the result into a dictionary
    keys = ["designation", "ra", "dec", "b", "l", "grvs_mag", "distance_gspphot"]
    star_data = [dict(zip(keys, row)) for row in result]

    return star_data


@app.route("/preview")
def preview():
    return render_template("preview.html")


@app.route("/save_data", methods=["GET", "POST"])
def save_data():
    if request.method == "POST":
        return render_template("apology.html")
    else:
        return render_template("save_data.html")


@app.route("/upload", methods=["GET", "POST"])
def load_from_file():
    if request.method == "POST":
        return render_template("apology.html")
    else:
        return render_template("load_from_file.html")


if __name__ == "__main__":
    app.run(debug=True)
