# Carmain Service Description

Carmain is a web application for vehicle maintenance management that allows users to track service history and receive reminders about scheduled maintenance procedures.

## Key Features:

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

## Architecture:

- Modern web application built with FastAPI and SQLAlchemy ORM
- Interactive interface using HTMX and Bootstrap
- Implementation of business logic through a service layer and repository pattern
- User management system (registration, authorization)
- Administrative panel for data management

Carmain helps vehicle owners:
- Never miss important scheduled maintenance
- Maintain a complete vehicle service history
- Optimize maintenance expenses
- Keep their vehicles in good technical condition

The interface features a yellow color scheme, which is associated with automotive themes.