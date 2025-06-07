# Django Airport Management System

A comprehensive airport management system built with Django, featuring flight management, booking system, passenger services, and administrative tools.

## Features

- **User Management**: Multi-role user system (Admin, Staff, Airline Staff, Passengers)
- **Flight Management**: Create, update, and manage flights
- **Booking System**: Flight booking with seat selection
- **Passenger Services**: Check-in, boarding pass generation, baggage management
- **Notifications**: Real-time notifications and announcements
- **Dashboard**: Role-based dashboards with analytics
- **Reports**: Comprehensive reporting system

## Installation

### Prerequisites

- Python 3.10+
- MySQL/PostgreSQL (optional, SQLite included for development)
- Virtual Environment

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Airport
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Production dependencies
   pip install -r requirements.txt
   
   # Development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

4. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env file with your settings
   nano .env
   ```

5. **Database Setup**
   ```bash
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
Airport/
├── Airport/                 # Main project settings
├── users/                   # User management app
├── flights/                 # Flight management app
├── bookings/               # Booking system app
├── notifications/          # Notification system app
├── dashboard/              # Dashboard and analytics app
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User uploaded files
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
└── manage.py              # Django management script
```

## Usage

### User Roles

- **Admin**: Full system access, user management, system configuration
- **Staff**: Airport operations, flight management, passenger assistance
- **Airline Staff**: Airline-specific flight and booking management
- **Passenger**: Flight booking, check-in, boarding pass access

### Key URLs

- `/admin/` - Django Admin Panel
- `/users/profile/` - User Profile Management
- `/flights/` - Flight Search and Management
- `/bookings/` - Booking Management
- `/dashboard/` - Role-based Dashboard
- `/notifications/` - Notifications and Announcements

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

### Database Management
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## Deployment

### Production Settings

1. **Environment Variables**
   - Set `DEBUG=False`
   - Configure `ALLOWED_HOSTS`
   - Set secure `SECRET_KEY`
   - Configure database settings

2. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Security Checklist**
   ```bash
   python manage.py check --deploy
   ```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "Airport.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.
