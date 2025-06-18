# Solar Monitoring Dashboard

This project is a simple Flask application that allows you to monitor and store design data for solar panels. It uses a SQLite database to keep track of each panel's ID, location, and current power output.

## Features

- Add new solar panel records via a web form
- View existing data in a table
- Responsive layout using Bootstrap

## Requirements

- Python 3.8+
- `pip` package manager

## Setup

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python -m solar_dashboard.app
```

The app will start on <http://localhost:5000> by default.

## Project Structure

```
solar_dashboard/
├── app.py              # Flask application
├── templates/
│   └── index.html      # Dashboard page
└── static/             # Directory for future static assets
```

Feel free to extend the dashboard with additional pages or API endpoints as needed.
