Esta aplicación combina inteligencia artificial, análisis cuantitativo y simulación de opciones para ayudarte a gestionar y proteger tu portafolio como lo haría un gestor profesional.

## 🚀 Funcionalidades integradas

- 📊 **Gestor de portafolio**  
  Revisa tus posiciones, evalúa rentabilidad y sugiere cobertura o mantenimiento.

- 📈 **Simulador de opciones con Delta**  
  Calcula prima, payoff y probabilidad implícita de éxito según tu perfil de riesgo (CALL o PUT).

- 📉 **Dashboard de desempeño histórico**  
  Analiza decisiones pasadas con visualizaciones de rentabilidad por ticker y acción tomada.

- 📈 **Backtesting Darvas que nos presenta esta estrategia**
  Realiza un backtesting de la estrategia de Darvas
  
- 📊 **Top Volumen 30d**
  Lista tickers cuyo volumen aumentó 50% o más en los últimos 30 días

- 🔗 **Conexión Schwab**
  Prueba la API oficial para consultar tus cuentas

## ⚙️ Archivos clave

- `app.py`: archivo principal de la app (corre en Streamlit)
- `requirements.txt`: dependencias para correr en la nube
- `registro_acciones.csv`: log de decisiones tomadas (se genera automáticamente)
- `refresh_token.txt`: se crea al autenticarse con Schwab y almacena el refresh token de forma local

## ▶️ ¿Cómo correrlo?

### Localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Ejecutar pruebas
```bash
pip install -r requirements.dev.txt
pytest
```

Para usar la integración con Schwab deberás definir `CLIENT_ID`,
`CLIENT_SECRET` y `REFRESH_TOKEN` en tus secretos de Streamlit o en tus variables de entorno.

El `refresh_token` obtenido se guarda en el archivo `refresh_token.txt` en la raíz del proyecto. Este archivo se crea automáticamente con permisos `600` para que solo el usuario actual pueda leerlo y escribirlo.

Si falta cualquiera de estas credenciales la aplicación lanzará
`RuntimeError("Missing Schwab API credentials")` antes de intentar conectarse.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
