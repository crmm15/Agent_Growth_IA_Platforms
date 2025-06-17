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

## ⚙️ Archivos clave

- `app.py`: archivo principal de la app (corre en Streamlit)
- `requirements.txt`: dependencias para correr en la nube
- `registro_acciones.csv`: log de decisiones tomadas (se genera automáticamente)

## ▶️ ¿Cómo correrlo?

### Localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```
