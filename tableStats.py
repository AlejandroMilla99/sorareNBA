import os
import json
import locale
from datetime import datetime, timedelta
import subprocess
from app import run_chrome_window  # Import the function from app.py
from myPlayers import my_players, get_my_limited_cards, get_access_token, extract_player_slugs
import re
import copy
from flask import Flask, render_template, redirect, url_for, request
import requests

def reverseFormatMiles(cadena):
    return float(cadena.replace(".", "").replace(",", "."))

def reverseFormatDecimal(cadena):
    # Establecer la configuración regional para español
    locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')

    # Reemplazar el punto decimal por la coma
    cadena_con_coma = cadena.replace(".", ",")

    # Intentar convertir la cadena formateada a un número
    try:
        numero = locale.atof(cadena_con_coma)
        return numero
    except ValueError:
        # En caso de error, devolver None o lanzar una excepción según sea necesario
        return None

def formatMiles(numero):
    return "{:,}".format(numero).replace(",", ".")

def formatDecimal(numero):
    # Establecer la configuración regional para español
    locale.setlocale(locale.LC_ALL, 'es_ES.utf-8')
    # Formatear el número como cadena con el formato local
    numero_formateado = locale.format_string("%.2f", numero)
    return numero_formateado

def optimize_team(players, max_cap, isContender):
    n = len(players)

    def calculate_total_projection(subset):
        return sum(player['projectionScore'] for player in subset)

    memo = {}

    def find_optimal_combination(index, remaining_cap, selected_count):
        # Check if we have selected exactly 5 players
        if index == n or remaining_cap < 0 or selected_count > 5:
            return [] if selected_count != 5 else []

        memo_key = f'{index}-{remaining_cap}-{selected_count}-{isContender}'
        if memo_key in memo:
            return memo[memo_key]

        # Select the player with the highest projectionScore first if isContender is False
        if not isContender and selected_count == 0:
            contender_player = max(players, key=lambda x: x['projectionScore'])
            remaining_cap_contender = remaining_cap - contender_player['actualCap']
            if remaining_cap_contender >= 0:
                include_contender = [contender_player] + find_optimal_combination(index + 1, remaining_cap_contender, selected_count + 1)
                optimal_subset = max([[], include_contender], key=lambda x: calculate_total_projection(x))
                memo[memo_key] = optimal_subset
                return optimal_subset

        # Exclude the current player
        exclude_current = find_optimal_combination(index + 1, remaining_cap, selected_count)

        # Include the current player if their actualCap does not exceed the limit
        include_current = (
            [players[index]] + find_optimal_combination(index + 1, remaining_cap - players[index]['actualCap'], selected_count + 1)
        ) if remaining_cap >= players[index]['actualCap'] else []

        # Compare and select the combination with the maximum sum of projectionScore
        optimal_subset = max([exclude_current, include_current], key=lambda x: calculate_total_projection(x))

        memo[memo_key] = optimal_subset
        return optimal_subset

    return find_optimal_combination(0, max_cap, 0)





# Ruta al archivo datos_jugadores.json desde la raíz del proyecto
ruta_archivo = "datos_jugadores_updated.json"
contMyPlayers = 0
contPlayers = 0
 # Lista para almacenar datos de jugadores
datos_jugadores = []

# Lista para almacenar datos de jugadores
datos_myplayers = []

# Intentar abrir y leer el archivo JSON
try:
    with open(ruta_archivo, "r") as archivo:
        # Cargar el contenido del archivo JSON en una variable
        json_jugadores_raw = json.load(archivo)
        json_jugadores = json_jugadores_raw.get("jugadores", {})
        # Agregar cada jugador a la lista
        for jugador in json_jugadores:
            datos_jugadores.append({"jugador": jugador})
        contPlayers = len(datos_jugadores)
except FileNotFoundError:
    # Manejar el caso en el que el archivo no se encuentre
    print(f"Error: No se encontró el archivo {ruta_archivo}")



actionFilter = "bigdataFiltered.html"
redirectClearFilter = "bigdata.html"

ruta_archivo2 = "datos_jugadores_my_players.json"
# Intentar abrir y leer el archivo JSON
try:
    with open(ruta_archivo2, "r") as archivo:
        # Cargar el contenido del archivo JSON en una variable
        json_myplayers_raw = json.load(archivo)
        json_myplayers = json_myplayers_raw.get("jugadores", {})
        # Agregar cada jugador a la lista
        for jugador in json_myplayers:
            datos_myplayers.append({"jugador": jugador})
        contMyPlayers = len(datos_myplayers)
except FileNotFoundError:
    # Manejar el caso en el que el archivo no se encuentre
    print(f"Error: No se encontró el archivo {ruta_archivo2}")


def tabling(json_modificado, json_filters, actionFilter, redirectClearFilter, ruta_archivo):

    contMyPlayers = 0
    contPlayers = 0
    # Lista para almacenar datos de jugadores
    datos_jugadores = []
    datos_myplayers = []

    try:
        with open(ruta_archivo, "r") as archivo:
            # Cargar el contenido del archivo JSON en una variable
            json_jugadores_raw = json.load(archivo)
            json_jugadores = json_modificado.get("jugadores", {})
                # Agregar cada jugador a la lista
            for jugador in json_jugadores:
                datos_jugadores.append({"jugador": jugador})
            contPlayers = len(datos_jugadores)
    except FileNotFoundError:
        # Manejar el caso en el que el archivo no se encuentre
        print(f"Error: No se encontró el archivo {ruta_archivo}")

    if actionFilter == "myplayersFiltered.html":
        # Intentar abrir y leer el archivo JSON
        try:
            with open(ruta_archivo2, "r") as archivo:
                # Cargar el contenido del archivo JSON en una variable
                json_myplayers_raw = json.load(archivo)
                json_myplayers = json_modificado.get("jugadores", {})
                print("AKII")
                # Agregar cada jugador a la lista
                for jugador in json_myplayers:
                    datos_myplayers.append({"jugador": jugador})
                contMyPlayers = len(datos_myplayers)
        except FileNotFoundError:
            # Manejar el caso en el que el archivo no se encuentre
            print(f"Error: No se encontró el archivo {ruta_archivo2}")
    
    if ruta_archivo == "datos_jugadores_my_players.json":
        contMyPlayers = len(datos_myplayers)
        print("AKII")
        print(contMyPlayers)
        contPlayers = contMyPlayers


    # Crear una tabla HTML
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <!-- Resto de tus etiquetas head y estilos CSS -->
            <link rel="stylesheet" href="{{ url_for('static', filename='estilo.css') }}">
            <link href="//netdna.bootstrapcdn.com/font-awesome/3.2.1/css/font-awesome.css" rel="stylesheet">
            <script src="https://kit.fontawesome.com/9575b918a2.js" crossorigin="anonymous"></script>
    </head>

    <input type="text" id="searchInput" placeholder=" &#x1F50D">
    <div class="search-results" id="searchResults" style="position: absolute; color:white"></div>

    <!-- Resto de tu código HTML -->

    <script>
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        var enfocar = false;

        const jugadores = {{ jugadores | tojson | safe }};

        // Restricción: Permitir solo letras y espacios
        searchInput.addEventListener('input', function () {
            const searchText = this.value.toLowerCase();
            enfocar = true
            const filteredPlayers = jugadores.filter(player => player.name.toLowerCase().includes(searchText));
            renderSearchResults(filteredPlayers);
        });

        searchInput.addEventListener('blur', function () {
            // Borra el contenido del campo de búsqueda cuando pierde el enfoque
            if(enfocar == false){
                this.value = '';
                searchResults.style.display = 'none'; // Oculta la lista de resultados
                searchResults.innerHTML = ''; // Borra el contenido de la lista
            }
            else{
                
                enfocar = false;
            }
        });

        // Cuando el mouse entra en los resultados
        searchResults.addEventListener('mouseover', function () {
            // Dar el enfoque al campo de búsqueda
            searchInput.focus();
            enfocar = true;
            
        });

    function renderSearchResults(results) {
        if (results.length === 0 || searchInput.value === '') {
            searchResults.style.display = 'none';
            searchResults.innerHTML = '';
            enfocar = false;
            return;
        }

        const resultList = document.createElement('ul');
        resultList.style.marginLeft = '25%';
        resultList.style.marginTop = '3%';
        results.forEach(player => {
            const listItem = document.createElement('li');
            listItem.style.width = '160px';
            listItem.style.cursor = 'pointer';

            // Agrega un enlace al jugador
            const playerLink = document.createElement('a');
            playerLink.href = `/${player.name}`; // Usa el name del jugador para construir la URL
            playerLink.textContent = player.name;
            playerLink.style.marginLeft = '5%';

            // Agrega un evento de clic al elemento <li> para redirigir al usuario
            listItem.addEventListener('click', function () {
                window.location.href = playerLink.href;
            });

            listItem.appendChild(playerLink);
            resultList.appendChild(listItem);
        });

        searchResults.innerHTML = '';
        searchResults.appendChild(resultList);
        searchResults.style.display = 'block';
    }

    </script>


    <!-- Resto de tu código HTML -->

    <script>
    var table;
    var columnSortDirections = Array(7).fill("asc");
    var currentPage = 1;
    var rowsPerPage = 10;
    var contVerMas = 0;

    function initTable() {
        table = document.getElementById("jugadoresTable");
    }



    function reverseFormatDecimal(cadena) {
    // Reemplazar la coma por el punto decimal
    var cadena_con_punto = cadena.replace(",", ".");

    // Intentar convertir la cadena formateada a un número
    var numero = parseFloat(cadena_con_punto);

    // Verificar si la conversión fue exitosa
    if (!isNaN(numero)) {
        return numero;
    } else {
        // En caso de error, devolver NaN o lanzar una excepción según sea necesario
        return null;
    }
    }

    function reverseFormatMiles(cadena) {
    // Eliminar los puntos y reemplazar la coma por el punto decimal
    var cadena_sin_puntos = cadena.replace(/\./g, "");

    // Intentar convertir la cadena formateada a un número
    var numero = parseInt(cadena_sin_puntos);

    return numero;
    }

    // ... (Tu código existente)



        function sortTable(columnIndex) {
        var dir = columnSortDirections[columnIndex];
        
        var compareFunction;
        if (columnIndex < 2 || columnIndex > 10) {
            // Columnas 0 , 1, 11, 12 (names y Equipos): Ordenación alfabética
            compareFunction = function (a, b) {
                var aValue = a.cells[columnIndex].textContent.toLowerCase();
                var bValue = b.cells[columnIndex].textContent.toLowerCase();
                return dir === "desc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
            };
        } 
         else {
                    // Otras columnas: Ordenación numérica
            if (columnIndex === 2 || columnIndex === 3) {
                compareFunction = function (a, b) {
                    // Elimina caracteres no numéricos al principio de la cadena
                    var regex = /[\€,]/;
                    var aValue = reverseFormatMiles(a.cells[columnIndex].textContent.replace(regex, ""));
                    var bValue = reverseFormatMiles(b.cells[columnIndex].textContent.replace(regex, ""));
                    return dir === "asc" ? aValue - bValue : bValue - aValue;
                };
            }
            else if (columnIndex === 4){
                    compareFunction = function (a, b) {
                        var aValue = parseFloat(a.cells[columnIndex].textContent.replace(/[^0-9.-]+/g,""));
                        var bValue = parseFloat(b.cells[columnIndex].textContent.replace(/[^0-9.-]+/g,""));
                        return dir === "asc" ? aValue - bValue : bValue - aValue;
                };
            }
            else {
                compareFunction = function (a, b) {
                var aValue = parseFloat(a.cells[columnIndex].textContent.replace(/[^0-9.-]+/g,""));
                var bValue = parseFloat(b.cells[columnIndex].textContent.replace(/[^0-9.-]+/g,""));
                    return dir === "asc" ? aValue - bValue : bValue - aValue;
                };
            }
         }

        var rows = Array.from(table.rows).slice(1);
        rows.sort(compareFunction);

        for (var i = 0; i < rows.length; i++) {
            table.tBodies[0].appendChild(rows[i]);
        }

        // Cambia las flechas de ordenamiento en las columnas
        var headers = table.getElementsByTagName("th");
        for (var i = 0; i < headers.length; i++) {
            var span = headers[i].getElementsByTagName("span")[0];
            if (span) {
                span.innerHTML = "";
            }
        }
        var currentHeader = headers[columnIndex];
        var span = currentHeader.getElementsByTagName("span")[0];
        if (!span) {
            span = document.createElement("span");
            currentHeader.appendChild(span);
        }
        span.innerHTML = dir === "asc" ? "&#8595;" : "&#8593;";

        // Cambia la dirección de orden actual
        columnSortDirections[columnIndex] = dir === "asc" ? "desc" : "asc";
        currentPage = 1;
        rowsPerPage = 10;
        contVerMas = 0;
    }

    </script>

    



    <title>Tabla de Jugadores</title>
    </head>
    <body onload="initTable()">

    """

    html += f"""
    <div class='act' id="actu" style="display: none"> </div>
    <div id="loader">
        <div id="progress"></div>
        <h4 style="margin-top: 2%; margin-left: 14%; color: red; font-size: x-large; font-weight: bold" id="loadText"></h4>
    </div>
    <div style="white-space: nowrap; text-align: center; position: relative; z-index: 99; margin-bottom: 1%;">
        <h2 style="color: white; font-size: x-large; padding: 1%; margin-top: revert;">Last Update: {json_jugadores_raw.get("date", {})}</h2>
        {'<a id="updateButton" href="bigdataUpdated.html"><span style="color:white">Update</span></a>' if ruta_archivo == "datos_jugadores_updated.json" else '<div class="oauth-button-container" style="text-align: center; margin-top: 20px; margin-bottom: 20px;"> <a style="color:white" href="https://sorare.com/oauth/authorize?client_id=kni0hLKjFQTChnBQEBzbb36l7y79Ua7nMDBgaHwoKSk&redirect_uri=http://localhost:5000/auth/sorare&response_type=code&scope="> Sign in with Sorare </a> </div>	'}
    </div>
    <div>
    <form id="filterForm" action={actionFilter} method="get">
        <div id="filters-div" style="display: none">

        <div class="range_container">
        <label style="color: white; text-align: center; margin-bottom: 10%;" for="priceFilter">Price</label>
                <div class="sliders_control">
                    <input id="fromSliderPrice" type="range"   value="0" min="-1" max="300"/>
                    <input id="toSliderPrice" type="range" value="300" min="-1" max="300"/>
                </div>
                <div class="form_control">
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Min</div>
                        <input class="form_control_container__time__input" type="number" id="fromInputPrice" name="fromInputPrice" step="0.01" value="0" min="-1" max="300"/>
                    </div>
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Max</div>
                        <input class="form_control_container__time__input" type="number" id="toInputPrice" name="toInputPrice" step="0.01" value="300" min="-1" max="300"/>
                    </div>
                </div>
            </div>

            <div class="range_container">
            <label style="color: white; text-align: center; margin-bottom: 10%;" for="CapFilter">Cap</label>
                <div class="sliders_control">
                    <input id="fromSliderCap" type="range" value="0" min="-3" max="80"/>
                    <input id="toSliderCap" type="range" value="80" min="-3" max="80"/>
                </div>
                <div class="form_control">
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Min</div>
                        <input class="form_control_container__time__input" type="number" id="fromInputCap" name="fromInputCap" value="0" min="-3" max="80"/>
                    </div>
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Max</div>
                        <input class="form_control_container__time__input" type="number" id="toInputCap" name="toInputCap" value="80" min="-3" max="80"/>
                    </div>
                </div>
            </div>

            <div class="range_container">
                <label style="color: white; text-align: center; margin-bottom: 10%;" for="projFilter">Proj</label>
                <div class="sliders_control">
                    <input id="fromSliderProj" type="range" value="0" min="-3" max="80"/>
                    <input id="toSliderProj" type="range" value="80" min="-3" max="80"/>
                </div>
                <div class="form_control">
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Min</div>
                        <input class="form_control_container__time__input" type="number" id="fromInputProj" name="fromInputProj" value="0" min="-3" max="80"/>
                    </div>
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Max</div>
                        <input class="form_control_container__time__input" type="number" id="toInputProj" name="toInputProj"  value="80" min="-3" max="80"/>
                    </div>
                </div>
            </div>

            <div class="range_container">
                <label style="color: white; text-align: center; margin-bottom: 10%;" for="ratioPuteFilter">RatioPute</label>
                <div class="sliders_control">
                    <input id="fromSliderRatioPute" type="range" value="0" min="-2" max="20"/>
                    <input id="toSliderRatioPute" type="range" value="20" min="-2" max="20"/>
                </div>
                <div class="form_control">
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Min</div>
                        <input class="form_control_container__time__input" type="number" id="fromInputRatioPute" name="fromInputRatioPute" step="0.01" value="0" min="-2" max="20"/>
                    </div>
                    <div class="form_control_container" style="text-align: center">
                        <div class="form_control_container__time">Max</div>
                        <input class="form_control_container__time__input" type="number" id="toInputRatioPute" name="toInputRatioPute" step="0.01" value="20" min="-2" max="20"/>
                    </div>
                </div>
            </div>

            <div style="color: white; font-size: 18px; position: relative; top: 28px; left: 20px;">
                GW finished: 
                <input type="checkbox" id="gwFinishedCheckbox" name="gwFinishedCheckbox">
            </div>
    </div>

    </div>
    <div id="buttonsFilter" style="text-align: left; display: none">
        <button id="applyFilter" style="width: 9%;" type="submit">Apply filters</button>
        <a style="color: white" href={redirectClearFilter} id="clearFilter" type="button" onclick="clearFilters()">Remove filters</a>
    </div>
    </form>
    <div style="text-align: left; margin-top: -2%; margin-left: -0.8%; width: 95%; display: flex">
     <button id="dismissFilter" style="display: none; margin-left: 3%; margin-top: 3.3%;   position: relative;" onclick="dismissFilters()">Hide Filters</button>
     <button id="showFilter" style="margin-left: 3%; margin-top: 3.3%;"  onclick="showFilters()">Show filters</button>
     <h1 style="color: white; color: white; position: relative; left: 75%; top: 50px;">Nº Players: {contPlayers}</h1>
     <!-- Comienzo Informacion del filtro aplicado -->

     <!-- Fin Informacion del filtro aplicado -->

    </div>

    <div id="table-container">
    
    <table id="jugadoresTable" border="1">
        <tr>
            <th onclick="sortTable(0)" class="active">Name<span></span></th>
            <th onclick="sortTable(1)" class="active">Team<span></span></th>
            <th onclick="sortTable(2)" class="active">Price €<span></span></th>
            <th onclick="sortTable(3)" class="active">Actual Cap<span></span></th>
            <th onclick="sortTable(4)" class="active">Future Cap<span></span></th>
            <th onclick="sortTable(5)" class="active">Difference Cap<span></span></th>
            <th onclick="sortTable(6)" class="active">Projection<span></span></th>
            <th onclick="sortTable(7)" class="active">Cap Ratio<span></span></th>
            <th onclick="sortTable(8)" class="active">Proj Ratio<span></span></th>
            <th onclick="sortTable(9)" class="active">RatioPute<span></span></th>
            <th onclick="sortTable(10)" class="active">Games<span></span></th>
            <th onclick="sortTable(11)" class="active">On shape?<span></span></th>
            <th onclick="sortTable(12)" class="active">GW Finished?<span></span></th>
        </tr>
        <!-- Filas de datos aquí -->

        

    """
    html += """
    <script>
    function controlFromInput(fromSlider, fromInput, toInput, controlSlider) {
    const [from, to] = getParsed(fromInput, toInput);
    fillSlider(fromInput, toInput, '#C6C6C6', '#25daa5', controlSlider);
    if (from > to) {
        fromSlider.value = to;
        fromInput.value = to;
    } else {
        fromSlider.value = from;
    }
}
    
function controlToInput(toSlider, fromInput, toInput, controlSlider, sliderString) {
    const [from, to] = getParsed(fromInput, toInput);
    fillSlider(fromInput, toInput, '#C6C6C6', '#25daa5', controlSlider);
    setToggleAccessible(toInput, sliderString);
    if (from <= to) {
        toSlider.value = to;
        toInput.value = to;
    } else {
        toInput.value = from;
    }
}

function controlFromSlider(fromSlider, toSlider, fromInput) {
  const [from, to] = getParsed(fromSlider, toSlider);
  fillSlider(fromSlider, toSlider, '#C6C6C6', '#25daa5', toSlider);
  if (from > to) {
    fromSlider.value = to;
    fromInput.value = to;
  } else {
    fromInput.value = from;
  }
}

function controlToSlider(fromSlider, toSlider, toInput, sliderString) {
  const [from, to] = getParsed(fromSlider, toSlider);
  fillSlider(fromSlider, toSlider, '#C6C6C6', '#25daa5', toSlider);
  setToggleAccessible(toSlider, sliderString);
  if (from <= to) {
    toSlider.value = to;
    toInput.value = to;
  } else {
    toInput.value = from;
    toSlider.value = from;
  }
}

function getParsed(currentFrom, currentTo) {
  const from = parseFloat(currentFrom.value, 10);
  const to = parseFloat(currentTo.value, 10);
  console.log([from, to]);
  return [from, to];
}

function fillSlider(from, to, sliderColor, rangeColor, controlSlider) {
    const rangeDistance = to.max-to.min;
    const fromPosition = from.value - to.min;
    const toPosition = to.value - to.min;
    controlSlider.style.background = `linear-gradient(
      to right,
      ${sliderColor} 0%,
      ${sliderColor} ${(fromPosition)/(rangeDistance)*100}%,
      ${rangeColor} ${((fromPosition)/(rangeDistance))*100}%,
      ${rangeColor} ${(toPosition)/(rangeDistance)*100}%, 
      ${sliderColor} ${(toPosition)/(rangeDistance)*100}%, 
      ${sliderColor} 100%)`;
}

function setToggleAccessible(currentTarget, sliderString) {
  const toSlider = document.querySelector(sliderString);
  if (Number(currentTarget.value) <= 0 ) {
    toSlider.style.zIndex = 2;
  } else {
    toSlider.style.zIndex = 0;
  }
}

const fromSliderPrice = document.querySelector('#fromSliderPrice');
const toSliderPrice = document.querySelector('#toSliderPrice');
const fromInputPrice = document.querySelector('#fromInputPrice');
const toInputPrice = document.querySelector('#toInputPrice');
const sliderStringPrice = '#toSliderPrice';

fillSlider(fromSliderPrice, toSliderPrice, '#C6C6C6', '#25daa5', toSliderPrice);
setToggleAccessible(toSliderPrice, sliderStringPrice);
fromSliderPrice.oninput = () => controlFromSlider(fromSliderPrice, toSliderPrice, fromInputPrice);
toSliderPrice.oninput = () => controlToSlider(fromSliderPrice, toSliderPrice, toInputPrice, sliderStringPrice);
fromInputPrice.oninput = () => controlFromInput(fromSliderPrice, fromInputPrice, toInputPrice, toSliderPrice);
toInputPrice.oninput = () => controlToInput(toSliderPrice, fromInputPrice, toInputPrice, toSliderPrice, sliderStringPrice);

const fromSliderCap = document.querySelector('#fromSliderCap');
const toSliderCap = document.querySelector('#toSliderCap');
const fromInputCap = document.querySelector('#fromInputCap');
const toInputCap = document.querySelector('#toInputCap');
const sliderStringCap = '#toSliderCap';

fillSlider(fromSliderCap, toSliderCap, '#C6C6C6', '#25daa5', toSliderCap);
setToggleAccessible(toSliderCap, sliderStringCap);
fromSliderCap.oninput = () => controlFromSlider(fromSliderCap, toSliderCap, fromInputCap);
toSliderCap.oninput = () => controlToSlider(fromSliderCap, toSliderCap, toInputCap, sliderStringCap);
fromInputCap.oninput = () => controlFromInput(fromSliderCap, fromInputCap, toInputCap, toSliderCap);
toInputCap.oninput = () => controlToInput(toSliderCap, fromInputCap, toInputCap, toSliderCap, sliderStringCap);

const fromSliderProj = document.querySelector('#fromSliderProj');
const toSliderProj = document.querySelector('#toSliderProj');
const fromInputProj = document.querySelector('#fromInputProj');
const toInputProj = document.querySelector('#toInputProj');
const sliderStringProj = '#toSliderProj';

fillSlider(fromSliderProj, toSliderProj, '#C6C6C6', '#25daa5', toSliderProj);
setToggleAccessible(toSliderProj, sliderStringProj);
fromSliderProj.oninput = () => controlFromSlider(fromSliderProj, toSliderProj, fromInputProj);
toSliderProj.oninput = () => controlToSlider(fromSliderProj, toSliderProj, toInputProj, sliderStringProj);
fromInputProj.oninput = () => controlFromInput(fromSliderProj, fromInputProj, toInputProj, toSliderProj);
toInputProj.oninput = () => controlToInput(toSliderProj, fromInputProj, toInputProj, toSliderProj, sliderStringProj);

const fromSliderRatioPute = document.querySelector('#fromSliderRatioPute');
const toSliderRatioPute = document.querySelector('#toSliderRatioPute');
const fromInputRatioPute = document.querySelector('#fromInputRatioPute');
const toInputRatioPute = document.querySelector('#toInputRatioPute');
const sliderStringRatioPute = '#toSliderRatioPute';

fillSlider(fromSliderRatioPute, toSliderRatioPute, '#C6C6C6', '#25daa5', toSliderRatioPute);
setToggleAccessible(toSliderRatioPute, sliderStringRatioPute);
fromSliderRatioPute.oninput = () => controlFromSlider(fromSliderRatioPute, toSliderRatioPute, fromInputRatioPute);
toSliderRatioPute.oninput = () => controlToSlider(fromSliderRatioPute, toSliderRatioPute, toInputRatioPute, sliderStringRatioPute);
fromInputRatioPute.oninput = () => controlFromInput(fromSliderRatioPute, fromInputRatioPute, toInputRatioPute, toSliderRatioPute);
toInputRatioPute.oninput = () => controlToInput(toSliderRatioPute, fromInputRatioPute, toInputRatioPute, toSliderRatioPute, sliderStringRatioPute);


    </script>

    <script>

    function dismissFilters() {
            // Obtén el elemento div con id "filters-div"
            var filterDiv = document.getElementById("filters-div");
            var buttonsDiv = document.getElementById("buttonsFilter");
            var buttonDismiss = document.getElementById("dismissFilter");
            var buttonShow = document.getElementById("showFilter");

            // Oculta el div cambiando su estilo display a "none"
            filterDiv.style.display = "none";
            buttonsDiv.style.display = "none";
            buttonDismiss.style.display = "none";
            buttonShow.style.display = "";
        }

            function showFilters() {
            // Obtén el elemento div con id "filters-div"
            var filterDiv = document.getElementById("filters-div");
            var buttonsDiv = document.getElementById("buttonsFilter");
            var buttonDismiss = document.getElementById("dismissFilter");
            var buttonShow = document.getElementById("showFilter");

            // Muestra el div cambiando su estilo display a ""
            filterDiv.style.display = "flex";
            buttonsDiv.style.display = "";
            buttonDismiss.style.display = "";
            buttonShow.style.display = "none";
        }

    function clearFilters() {
        // Lógica para borrar los filtros
        document.getElementById("filterForm").reset();
        // También puedes añadir aquí lógica adicional para limpiar los resultados mostrados
    }


       
    </script>

    """
    
    # Agrega filas para cada jugador

    for jugador in datos_jugadores:
        jugador_data = jugador.get("jugador", {})  # Obtiene los datos del jugador del JSON
        # Verifica si hay datos del jugador
        if jugador_data:
            html += f"<tr onclick=\"window.location.href='/{jugador_data.get('name', '')}'\" style='cursor: pointer;'>"
            for clave, valor in jugador_data.items():
                if isinstance(valor, str):
                    if clave == "name":  # Comprueba si es el name del jugador
                        # Agrega un enlace al detalle del jugador usando el name
                        html += f"<td><a href='/{valor}'>{valor}</a></td>"                 
                    elif clave == "teamAvatarUrl":
                        if valor == "No":
                            html += f"<td><i style='font-size: xx-large' class='fa fa-times' aria-hidden='true'></i><span style='display:none;'>{valor}</span></td>"
                        else:
                            html += f"<td><img src={valor} style='width:55px;'><span style='display:none;'>{valor}</span></td>"
                    elif clave == "projectionScore":  # Comprueba si es el name del jugador
                        html += f"<td>{int(valor)}</td>"
                    elif clave == "isInjured":  # Comprueba si es clave injured
                        if valor == "No":
                            html += "<td><i style='color: green; font-size: 2em;'  class='icon-ok-sign'></i><span style='display:none;'>aok</span></td>"
                        elif valor.startswith("Out"):
                            # Escapa las comillas simples dentro del valor usando backslashes
                            valor_escaped = valor.replace("'", "\\'")
                            html += f"<td><i onmouseover=\"mostrarTooltip(this.parentNode, '{valor_escaped}')\" onmouseout=\"ocultarTooltip(this)\" style='color: red; font-size: 2em;'  class='icon-plus-sign-alt'></i><span style='display:none;'>cout</span></td>"
                        else:
                            # Escapa las comillas simples dentro del valor usando backslashes
                            valor_escaped = valor.replace("'", "\\'")
                            html += f"<td><i onmouseover=\"mostrarTooltip(this.parentNode, '{valor_escaped}')\" onmouseout=\"ocultarTooltip(this)\" style='color: orange; font-size: 2em;'  class='fas fa-exclamation-triangle'></i><span style='display:none;'>bgtd</span></td>" 
                else:
                    if clave == "floorPrice":  # Comprueba si es el name del jugador
                        html += f"<td><span style='font-weight: bold'>{round(valor, 2)} €</span></td>"                    
                    if clave == "actualCap":  # Comprueba si es el name del jugador
                        html += f"<td>{valor}</td>"
                    elif clave == "futureCap":  # Comprueba si es el name del jugador
                        html += f"<td>{valor}</td>"
                    elif clave == "gamesOnNextGW":  # Comprueba si es el name del jugador
                        html += f"<td>{valor}</td>"
                    elif clave == "differenceCap":  # Comprueba si es el name del jugador
                        html += f"<td>{valor}</td>"
                    elif clave == "projectionScore":  # Comprueba si es el name del jugador
                        html += f"<td>{int(valor)}</td>"
                    elif clave == "capRatio":  # Comprueba si es el name del jugador
                        html += f"<td>{formatDecimal(valor)}</td>"
                    elif clave == "projRatio":  # Comprueba si es el name del jugadors
                        html += f"<td>{formatDecimal(valor)}</td>"    
                    elif clave == "finalRatio":  # Comprueba si es el name del jugadors
                        html += f"<td>{formatDecimal(valor)}</td>"                    
                    elif clave == "weekPoints":  # Comprueba si es el name del jugador
                        html += f"<td>{valor}</td>"
                    elif clave == "averagePoints":  # Comprueba si es el name del jugador
                        html += f"<td>{formatDecimal(valor)}</td>"
                    elif clave == "isGwFinished":  # Comprueba si es el name del jugador
                        if valor == True:
                            html += f"<td><span style='color: green; font-weight: bold'> <span>YES</span></td>"
                        else:
                            html += f"<td><span style='color: orange; font-weight: bold'> <span>NO</span></td>"          
                    
            html += "</tr>"

    html += "</table></div>"

    html +="""<script>
    // Función para mostrar el tooltip
    function mostrarTooltip(elemento, mensaje) {
        // Crear el elemento del tooltip
        const tooltip = document.createElement("div");
        tooltip.className = "tooltip";
        tooltip.textContent = mensaje;

        // Posicionar el tooltip al lado del icono
        const rect = elemento.getBoundingClientRect();
        tooltip.style.top = (rect.top + 24) + "px";
        tooltip.style.left = (rect.right - 60) + "px";

        // Agregar el tooltip al cuerpo del documento
        elemento.appendChild(tooltip);
    }

    // Función para ocultar el tooltip
    function ocultarTooltip(elemento) {
        // Buscar y eliminar el tooltip
        const tooltip = document.querySelector(".tooltip");
        if (tooltip) {
        tooltip.remove();
        }
    }
    </script>
    <script>
    const button = document.getElementById('updateButton');
    const loader = document.getElementById('loader');
    const progressBar = document.getElementById('progress');
    const mensajeLoad = document.getElementById('loadText');
    const actu = document.getElementById('actu');

    let progressWidth = 0;

    button.addEventListener('click', () => {
    loader.style.display = 'block';
    actu.style.display='flex';
    setTimeout(function(){
        loader.style.display = 'none';
        actu.style.display='none';
    }, 550000); // oculta el loader después de 55s

    fillProgress();
    });

    function fillProgress() {
    if (progressWidth >= 100) {
        return;
    } 
    if(progressWidth % 1 === 0)
        mensajeLoad.innerHTML = progressWidth + '%';
    
    progressWidth += 1;

    progressBar.style.width = `${progressWidth}%`;
    setTimeout(fillProgress, 4085);
    }
    </script>     
      
       
         """


    # Cargar la plantilla HTML desde el archivo
    with open("plantilla.html", "r") as plantilla_file:
        plantilla_html = plantilla_file.read()


    # Insertar el contenido específico en la zona de contenido de la plantilla
    plantilla_html = plantilla_html.replace("<!-- Contenido especifico de cada pagina ira aqui -->", html)

    # Guardar el HTML resultante en un archivo o usarlo como desees
    with open("bigdata.html", "w", encoding='utf-8') as pagina_file:
        pagina_file.write(plantilla_html)

    # Cargar el contenido de bigdata.html
    with open("bigdata.html", "r", encoding='utf-8') as bigdata_file:
        bigdata_html = bigdata_file.read()

    # Guardar el contenido de bigdata.html en un nuevo archivo bigdataUpdated.html
    with open("bigdataUpdated.html", "w", encoding='utf-8') as bigdataUpdated_file:
        bigdataUpdated_file.write(bigdata_html)

    # Guardar el contenido de bigdata.html en un nuevo archivo bigdataUpdated.html
    with open("bigdataFiltered.html", "w", encoding='utf-8') as bigdataFiltered_file:
        bigdataFiltered_file.write(bigdata_html)
    

    if (json_filters is not None):
        precio_min = json_filters.get("precio_min", "")
        precio_max = json_filters.get("precio_max", "")
        cap_min = json_filters.get("cap_min", "")
        cap_max = json_filters.get("cap_max", "")
        proj_min = json_filters.get("proj_min", "")
        proj_max = json_filters.get("proj_max", "")
        ratioPute_min = json_filters.get("ratioPute_min", "")
        ratioPute_max = json_filters.get("ratioPute_max", "") 
        GWFinished = json_filters.get("GWFinished", "") 

        # Leer el contenido actual del archivo bigdataFiltered.html
        with open("bigdataFiltered.html", "r", encoding='utf-8') as bigdataFiltered_file:
            contenido_actual = bigdataFiltered_file.read()
        # Definir el fragmento HTML que quieres añadir
        nuevo_contenido = f'''
            <div style="display: flex; flex-direction: row; justify-content: center; align-items: center;">
                <span style="margin-top: 20px; display: -webkit-inline-box; position: relative; z-index: 99;">
                    <p style="font-size: 18px; font-weight: bold; margin-top: 11px;">Players attributes: </p>
                    <span class="filter-indicator" style="  display: flex; flex-direction: row;"> <p style="color: #e74c3c;   font-size: 18px; font-weight: bold;">Price:&nbsp;</p> {precio_min} € - {precio_max} € </span>
                        <span class="filter-indicator" style="display: flex; flex-direction: row;">
                            <p style="color: #e74c3c; font-size: 18px; font-weight: bold;">Cap:&nbsp;</p>
                            {cap_min} - {cap_max}
                        </span>

                        <span class="filter-indicator" style="display: flex; flex-direction: row;">
                            <p style="color: #e74c3c; font-size: 18px; font-weight: bold;">Proj:&nbsp;</p>
                            {proj_min} - {proj_max}
                        </span>

                        <span class="filter-indicator" style="display: flex; flex-direction: row;">
                            <p style="color: #e74c3c; font-size: 18px; font-weight: bold;">RatioPute:&nbsp;</p>
                            {ratioPute_min} - {ratioPute_max}
                        </span>
                        <span class="filter-indicator" style="display: flex; flex-direction: row;">
                            <p style="color: #e74c3c; font-size: 18px; font-weight: bold;">{GWFinished}</p>
                        </span>
                    </span>
            </div>
        '''
        # Buscar el comentario y agregar el nuevo contenido justo debajo
        comentario = '<!-- Comienzo Informacion del filtro aplicado -->'
        posicion_comentario = contenido_actual.find(comentario)
        if posicion_comentario != -1:
            nuevo_contenido_html = contenido_actual[:posicion_comentario + len(comentario)] + '\n' + nuevo_contenido + contenido_actual[posicion_comentario + len(comentario):]
        else:
            # Si el comentario no se encuentra, simplemente agrega el nuevo contenido al final
            nuevo_contenido_html = contenido_actual + '\n' + nuevo_contenido

        # Escribir el nuevo contenido en el archivo
        with open("bigdataFiltered.html", "w", encoding='utf-8') as bigdataFiltered_file:
            bigdataFiltered_file.write(nuevo_contenido_html)

        
        # Cargar el contenido de bigdata.html
        with open("bigdataFiltered.html", "r", encoding='utf-8') as bigdata_file:
            bigdataFiltered_html = bigdata_file.read()
        # Guardar el contenido de bigdata.html en un nuevo archivo bigdataUpdated.html
        with open("myplayersFiltered.html", "w", encoding='utf-8') as myplayersFiltered_file:
            myplayersFiltered_file.write(bigdataFiltered_html)


    # Cargar la plantilla HTML desde el archivo
    with open("plantilla.html", "r") as plantilla_file:
        plantilla_html = plantilla_file.read()

    # Insertar el contenido específico en la zona de contenido de la plantilla
    plantilla_html = plantilla_html.replace("<!-- Contenido especifico de cada pagina ira aqui -->", html)

    # Guardar el HTML resultante en un archivo o usarlo como desees
    with open("myplayers.html", "w", encoding='utf-8') as pagina_file:
        pagina_file.write(plantilla_html)

# Obtiene la ruta completa del directorio actual
current_directory = os.path.abspath(os.path.dirname(__file__))

# Crea una instancia de la aplicación Flask y configura la ruta de las plantillas
app = Flask(__name__, template_folder=current_directory, static_url_path="/css")


@app.route('/<string:player_name>')
def player_detail(player_name):
    selected_player = None

    # Busca al jugador en datos_jugadores por su name
    for jugador in datos_jugadores:
        if jugador.get("jugador", {}).get("name") == player_name:
            selected_player = jugador
            break
        
    if selected_player:
        rp = selected_player.get("jugador", {}).get("pointsRegister", [])
        return render_template('plantillaJugador.html', player=selected_player, registroPuntos = rp)
    else:
        # Maneja el caso en el que no se encuentra el jugador
        return render_template('inicio.html')

@app.route('/bigdata.html')
def bigdata():
    with open(ruta_archivo, "r") as archivo:
    # Cargar el contenido del archivo JSON en una variable
        json_jugadores_raw = json.load(archivo)
    tabling(json_jugadores_raw, None, "bigdataFiltered.html", "bigdata.html", "datos_jugadores_updated.json")
    return render_template('bigdata.html', jugadores=json_jugadores)

@app.route('/bigdataFiltered.html')
def bigdataFiltered():

    # Obtener el valor del input de precio desde la solicitud
    precio_min = request.args.get('fromInputPrice', type=float)
    precio_max = request.args.get('toInputPrice', type=float)
    cap_min = request.args.get('fromInputCap', type=int)
    cap_max = request.args.get('toInputCap', type=int)
    proj_min = request.args.get('fromInputProj', type=int)
    proj_max = request.args.get('toInputProj', type=int)
    ratioPute_min = request.args.get('fromInputRatioPute', type=float)
    ratioPute_max = request.args.get('toInputRatioPute', type=float)
    gw_finished = request.args.get('gwFinishedCheckbox', type=bool)

    gwText = "GW finished" if gw_finished else "GW NOT finished"

    ruta_archivo = "datos_jugadores_updated.json"

    # Intentar abrir y leer el archivo JSON
    try:
        with open(ruta_archivo, "r") as archivo:
            # Cargar el contenido del archivo JSON en una variable
            json_jugadores_raw = json.load(archivo)
            json_jugadores = json_jugadores_raw.get("jugadores", {})
    except FileNotFoundError:
        # Manejar el caso en el que el archivo no se encuentre
        print(f"Error: No se encontró el archivo {ruta_archivo}")


    jugadores_filtrados = [
        jugador for jugador in json_jugadores_raw.get('jugadores', [])
        if (
            (precio_min is None or jugador.get('floorPrice', 0) >= precio_min) and
            (precio_max is None or jugador.get('floorPrice', 0) <= precio_max) and
            (cap_min is None or jugador.get('actualCap', 0) >= cap_min) and
            (cap_max is None or jugador.get('actualCap', 0) <= cap_max) and
            (proj_min is None or jugador.get('projectionScore', 0) >= proj_min) and
            (proj_max is None or jugador.get('projectionScore', 0) <= proj_max) and
            (ratioPute_min is None or jugador.get('finalRatio', 0) >= ratioPute_min) and
            (ratioPute_max is None or jugador.get('finalRatio', 0) <= ratioPute_max) and
            ((gw_finished is None) or (jugador.get('isGwFinished', False) == gw_finished))
        )
    ]

    # Crear un nuevo objeto JSON con la fecha original y los jugadores filtrados
    json_modificado = {
        "date": json_jugadores_raw.get('date'),
        "jugadores": jugadores_filtrados
    }
    json_filters = {
        "precio_min": precio_min,
        "precio_max": precio_max,
        "cap_min": cap_min,
        "cap_max": cap_max,
        "proj_min": proj_min,
        "proj_max": proj_max,
        "ratioPute_min": ratioPute_min,
        "ratioPute_max": ratioPute_max,
        "GWFinished": gwText
    }
    tabling(json_modificado, json_filters, "bigdataFiltered.html", "bigdata.html", "datos_jugadores_updated.json")
    return render_template('bigdataFiltered.html', jugadores=json_jugadores )

@app.route('/bigdataUpdated.html')
def bigdataUpdated():
    try:
        run_chrome_window()  # Call the function directly
    except Exception as e:
        print(f"Error al ejecutar app.py: {e}")
    # Ruta al archivo datos_jugadores.json desde la raíz del proyecto
    with open(ruta_archivo, "r") as archivo:
    # Cargar el contenido del archivo JSON en una variable
        json_jugadores_raw = json.load(archivo)
    tabling(json_jugadores_raw, None, "bigdataFiltered.html", "bigdata.html", "datos_jugadores_updated.json")
    return redirect(url_for('bigdata'))


@app.route('/inicio.html')
def inicio():
    # Tu lógica para la página de inicio.html
    return render_template('inicio.html')

@app.route('/miequipo.html')
def miequipo():
    # Ruta al archivo datos_jugadores.json desde la raíz del proyecto
    with open(ruta_archivo, "r") as archivo:
        # Cargar el contenido del archivo JSON en una variable
        json_jugadores_raw = json.load(archivo)
    # Leer el archivo JSON
    with open("optimal_lineups.json", "r") as json_file:
        optimal_lineups = json.load(json_file)
        # Extraer los valores de "optimalContender" y "optimalChampion"
        resultado_contender = optimal_lineups["optimalContender"]
        resultado_champion = optimal_lineups["optimalChampion"]
        resultado_combined = optimal_lineups["optimalCombined"]



    # Lista para almacenar datos de jugadores
    datos_jugadores = []

    # Agregar cada jugador a la lista
    for jugador in json_jugadores_raw.get("jugadores", []):
        datos_jugadores.append({"jugador": jugador})


    return render_template('miequipo.html', jugadoresL=datos_jugadores, resultadoContender=resultado_contender, resultadoChampion=resultado_champion, resultadoCombined = resultado_combined)

@app.route('/mybuilder.html')
def mybuilder():
    ruta_archivo2 = "datos_jugadores_my_players.json"
    # Ruta al archivo datos_jugadores.json desde la raíz del proyecto
    with open(ruta_archivo2, "r") as archivo:
        # Cargar el contenido del archivo JSON en una variable
        json_myplayers_raw = json.load(archivo)
    # Leer el archivo JSON
    with open("optimal_lineups.json", "r") as json_file:
        optimal_lineups = json.load(json_file)
        # Extraer los valores de "optimalContender" y "optimalChampion"
        resultado_contender = optimal_lineups["myOptimalContender"]
        resultado_champion = optimal_lineups["myOptimalChampion"]
        resultado_combined = optimal_lineups["myOptimalCombined"]


    # Lista para almacenar datos de jugadores
    datos_myplayers = []

    # Agregar cada jugador a la lista
    for jugador in json_myplayers_raw.get("jugadores", []):
        datos_myplayers.append({"jugador": jugador})


    return render_template('mybuilder.html', jugadoresL=datos_myplayers, resultadoContender=resultado_contender, resultadoChampion=resultado_champion, resultadoCombined = resultado_combined)

@app.route('/myplayers.html')
def myplayers():
    # Tu lógica para la página de myplayers.html
    with open("datos_jugadores_my_players.json", "r") as json_file:
        json_myPlayers = json.load(json_file)
        tabling(json_myPlayers, None, "myplayersFiltered.html", "myplayers.html", "datos_jugadores_my_players.json")
    return render_template('myplayers.html', jugadores = json_myplayers)

@app.route('/myplayersFiltered.html')
def myplayersFiltered():

    # Obtener el valor del input de precio desde la solicitud
    precio_min = request.args.get('fromInputPrice', type=float)
    precio_max = request.args.get('toInputPrice', type=float)
    cap_min = request.args.get('fromInputCap', type=int)
    cap_max = request.args.get('toInputCap', type=int)
    proj_min = request.args.get('fromInputProj', type=int)
    proj_max = request.args.get('toInputProj', type=int)
    ratioPute_min = request.args.get('fromInputRatioPute', type=float)
    ratioPute_max = request.args.get('toInputRatioPute', type=float)
    gw_finished = request.args.get('gwFinishedCheckbox', type=bool)

    gwText = "GW finished" if gw_finished else "GW NOT finished"

    ruta_archivo2 = "datos_jugadores_my_players.json"
    # Intentar abrir y leer el archivo JSON
    try:
        with open(ruta_archivo2, "r") as archivo:
            # Cargar el contenido del archivo JSON en una variable
            json_myplayers_raw = json.load(archivo)
            json_myplayers = json_myplayers_raw.get("jugadores", {})
    except FileNotFoundError:
        print("Error json_myplayers_raw")

    jugadores_filtrados = [
        jugador for jugador in json_myplayers_raw.get('jugadores', [])
        if (
            (precio_min is None or jugador.get('floorPrice', 0) >= precio_min) and
            (precio_max is None or jugador.get('floorPrice', 0) <= precio_max) and
            (cap_min is None or jugador.get('actualCap', 0) >= cap_min) and
            (cap_max is None or jugador.get('actualCap', 0) <= cap_max) and
            (proj_min is None or jugador.get('projectionScore', 0) >= proj_min) and
            (proj_max is None or jugador.get('projectionScore', 0) <= proj_max) and
            (ratioPute_min is None or jugador.get('finalRatio', 0) >= ratioPute_min) and
            (ratioPute_max is None or jugador.get('finalRatio', 0) <= ratioPute_max) and
            ((gw_finished is None) or (jugador.get('isGwFinished', False) == gw_finished))
        )
    ]

    # Crear un nuevo objeto JSON con la fecha original y los jugadores filtrados
    json_modificado = {
        "date": json_myplayers_raw.get('date'),
        "jugadores": jugadores_filtrados
    }
    json_filters = {
        "precio_min": precio_min,
        "precio_max": precio_max,
        "cap_min": cap_min,
        "cap_max": cap_max,
        "proj_min": proj_min,
        "proj_max": proj_max,
        "ratioPute_min": ratioPute_min,
        "ratioPute_max": ratioPute_max,
        "GWFinished": gwText
    }
    tabling(json_modificado, json_filters, "myplayersFiltered.html", "myplayers.html", "datos_jugadores_my_players.json")
    return render_template('myplayersFiltered.html', jugadores=json_myplayers)


client_id = "kni0hLKjFQTChnBQEBzbb36l7y79Ua7nMDBgaHwoKSk"
client_secret = "CgxjW3Ds4LW2JLsQPLfJJZDkX9CxV4iAmlWM6Tj9nrw"
redirect_uri = "http://localhost:5000/auth/sorare"

@app.route('/auth/sorare')
def auth_sorare():
    code = request.args.get('code')
    if code:
        access_token = get_access_token(client_id, client_secret, code, redirect_uri)
        limited_cards = get_my_limited_cards(access_token)
        player_slugs_myplayers = extract_player_slugs(limited_cards)
        
        my_players(player_slugs_myplayers)
        
        return redirect(url_for('myplayers'))
    else:
        # Redirect to Sorare OAuth if no code is present
        return redirect(f"https://sorare.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=")



if __name__ == '__main__':
    app.run(debug=True)
