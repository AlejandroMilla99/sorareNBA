# Define la estructura HTML común
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tu Sitio Web</title>
    <link rel="stylesheet" href="estilos.css"> <!-- Enlaza tu archivo CSS aquí -->
    <link rel="icon" href="{{ url_for('static', filename='img/favicon.ico') }}" type="image/x-icon">
</head>
<body>
    <!-- Barra de navegación -->
    <div class="menu">
        <ul>
            <li><a href="pagina_bigdata.html">Big Data</a></li>
            <li><a href="pagina_construccion_equipo.html">Construcción Equipo</a></li>
            <li><a href="pagina_predictor.html">Predictor</a></li>
        </ul>
    </div>

    <!-- Contenido de la página -->
    <div class="contenido">
        <!-- Contenido específico de cada página irá aquí -->
    </div>

    <!-- Pie de página -->
    <footer style="text-align: center; margin-top: 5%;" class="pie-de-pagina">
      <p style="font-weight: bold">Redes sociales</p>
      <div class="redes-sociales">
        <a href="https://www.linkedin.com/in/alejandro-milla-ram%C3%ADrez-3ba742209/"><img style="width: 2%;" src="{{ url_for('static', filename='img/linkedin.png') }}" alt="LinkedIn"></a>
        <a href="https://www.instagram.com/alex_milla99/"><img style="width: 2%;" src="{{ url_for('static', filename='img/instagram.png') }}" alt="Instagram"></a>
        <a href="mailto:alejandromilla99@gmail.com"><img style="width: 2%;" src="{{ url_for('static', filename='img/email.png') }}" alt="Correo Electrónico"></a>
      </div>
  </footer>
</body>
</html>
"""

# Guarda esta plantilla en un archivo HTML
with open("plantilla.html", "w") as file:
    file.write(html_template)

print("Plantilla HTML creada con éxito.")
