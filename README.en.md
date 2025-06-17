# Carmain - Vehicle Maintenance Management System

Carmain is a modern web application for vehicle maintenance management that allows users to track service history and receive reminders about scheduled maintenance procedures.

## Key Features

1. **Vehicle Management**
   - Registration and tracking of multiple vehicles in a single account
   - Storage of basic information: make, model, year, mileage

2. **Maintenance Management**
   - Catalog of typical maintenance procedures (MaintenanceItem)
   - Configuration of individual maintenance intervals for each vehicle
   - Tracking of the last date and mileage when work was performed

3. **Service Records**
   - Maintenance of a log of completed work (ServiceRecord)
   - Recording of service date, mileage, and comments for each procedure
   - History of all service procedures

4. **Reminder System**
   - Notifications about upcoming maintenance deadlines
   - Calculation of the next service date based on mileage/time

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy ORM, PostgreSQL
- **Frontend**: HTMX, Bootstrap 4.5, Jinja2 templates
- **Architecture**: Service layer, Repository pattern, Dependency Injection
- **Authentication**: FastAPI Users with cookie-based sessions
- **Admin Panel**: SQLAdmin for data management

## Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/carmain.git
   cd carmain
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start database**
   ```bash
   make dev
   # or
   docker-compose -f docker-compose.dev.yml up --build
   ```

5. **Run application (in separate terminal)**
   ```bash
   poetry run uvicorn carmain.main:carmain --reload --host 0.0.0.0 --port 8000
   ```

### Production Deployment

1. **Prepare environment**
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with production settings
   ```

2. **Deploy with Docker**
   ```bash
   make build-prod
   make up-prod
   ```

3. **Or manually**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Available Commands

```bash
make help           # Show all available commands
make dev           # Start development environment
make prod          # Start production environment
make build-prod    # Build production images
make logs          # Show production logs
make backup-db     # Backup production database
make clean         # Clean up containers and volumes
```

## Project Structure

```
carmain/
├── carmain/                 # Main application package
│   ├── admin/              # Admin panel configurations
│   ├── core/               # Core functionality (config, database, etc.)
│   ├── models/             # SQLAlchemy models
│   ├── repository/         # Data access layer
│   ├── routers/            # API routes
│   ├── schema/             # Pydantic schemas
│   ├── services/           # Business logic layer
│   ├── static/             # Static files (CSS, JS, images)
│   ├── templates/          # Jinja2 templates
│   ├── views/              # Web view controllers
│   └── main.py             # FastAPI application
├── docker-compose.dev.yml  # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
├── Dockerfile              # Development Dockerfile
├── Dockerfile.prod         # Production Dockerfile
├── nginx.conf              # Nginx configuration
└── Makefile               # Convenience commands
```

## Environment Variables

Key environment variables (see `.env.prod.example` for full list):

- `SECRET_KEY` - Application secret key
- `DB_NAME` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `ADMIN_EMAIL` - Administrator email

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.