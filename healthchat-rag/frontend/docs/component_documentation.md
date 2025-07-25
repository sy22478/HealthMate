# HealthChat RAG Dashboard - Component Documentation

## Overview
This document provides comprehensive documentation for all components in the HealthChat RAG Dashboard. Each component is documented with its props, methods, usage examples, and interaction guidelines.

## Table of Contents
1. [Authentication Components](#authentication-components)
2. [Layout Components](#layout-components)
3. [Dashboard Components](#dashboard-components)
4. [Health Profile Components](#health-profile-components)
5. [Chat Components](#chat-components)
6. [Metrics Components](#metrics-components)
7. [Reports Components](#reports-components)
8. [Settings Components](#settings-components)
9. [Interactive Components](#interactive-components)
10. [Performance Components](#performance-components)

---

## Authentication Components

### Login Page (`pages/login.py`)

**Purpose**: User authentication interface

**Props**: None (uses Streamlit session state)

**Methods**:
- `login_form()`: Renders the login form
- `validate_credentials(email, password)`: Validates user credentials
- `handle_forgot_password()`: Handles password reset request

**Usage Example**:
```python
import streamlit as st
from pages.login import login_form

# In your main app
if not st.session_state.get('authenticated'):
    login_form()
```

**Interaction Guidelines**:
- Email validation with proper format checking
- Password strength requirements
- "Remember Me" functionality
- Forgot password link
- Loading states during authentication

### Registration Page (`pages/register.py`)

**Purpose**: New user registration

**Props**: None

**Methods**:
- `registration_form()`: Renders the registration form
- `validate_registration_data(data)`: Validates registration data
- `create_user_account(data)`: Creates new user account

**Usage Example**:
```python
from pages.register import registration_form

# Show registration form
registration_form()
```

**Interaction Guidelines**:
- Real-time validation feedback
- Password strength indicator
- Terms and conditions acceptance
- Email verification process

### Password Reset (`pages/forgot_password.py`)

**Purpose**: Password recovery functionality

**Props**: None

**Methods**:
- `password_reset_form()`: Renders password reset form
- `send_reset_email(email)`: Sends password reset email

**Usage Example**:
```python
from pages.forgot_password import password_reset_form

# Show password reset form
password_reset_form()
```

---

## Layout Components

### Dashboard Header (`components/header.py`)

**Purpose**: Main application header with navigation and user controls

**Props**:
- `user_name` (str): Name of the current user
- `notification_count` (int): Number of unread notifications

**Methods**:
- `dashboard_header(user_name, notification_count)`: Renders the header

**Usage Example**:
```python
from components.header import dashboard_header

# Render header
dashboard_header("John Doe", 3)
```

**Interaction Guidelines**:
- Responsive design for mobile/desktop
- User profile dropdown menu
- Notification bell with badge
- Search functionality
- Theme toggle

### Sidebar Navigation (`components/sidebar.py`)

**Purpose**: Main navigation sidebar

**Props**: None

**Methods**:
- `dashboard_sidebar()`: Renders the sidebar navigation

**Usage Example**:
```python
from components.sidebar import dashboard_sidebar

# Render sidebar
dashboard_sidebar()
```

**Interaction Guidelines**:
- Collapsible navigation
- Active state highlighting
- Icon-based navigation
- Responsive behavior

### Breadcrumb Navigation (`components/breadcrumb.py`)

**Purpose**: Shows current page location in the application

**Props**:
- `breadcrumbs` (list): List of breadcrumb items
- `on_click` (callable, optional): Click handler for breadcrumb items

**Methods**:
- `breadcrumb_trail(breadcrumbs, on_click=None)`: Renders breadcrumb trail

**Usage Example**:
```python
from components.breadcrumb import breadcrumb_trail

# Render breadcrumbs
breadcrumb_trail(["Dashboard", "Health Profile", "Medical History"])
```

### Main Content Container (`components/main_content.py`)

**Purpose**: Main content area wrapper

**Props**: None

**Methods**:
- `main_content_container()`: Renders the main content area
- `grid_row(*sections)`: Creates a responsive grid row
- `show_loading()`: Shows loading state

**Usage Example**:
```python
from components.main_content import main_content_container, grid_row

with main_content_container():
    grid_row("Section 1", "Section 2", "Section 3")
```

### Footer (`components/footer.py`)

**Purpose**: Application footer with links and information

**Props**: None

**Methods**:
- `dashboard_footer()`: Renders the footer

**Usage Example**:
```python
from components.footer import dashboard_footer

# Render footer
dashboard_footer()
```

---

## Dashboard Components

### Quick Stats Cards (`components/quick_stats.py`)

**Purpose**: Display key health metrics overview

**Props**: None

**Methods**:
- `quick_stats_cards()`: Renders quick stats cards

**Usage Example**:
```python
from components.quick_stats import quick_stats_cards

# Display quick stats
quick_stats_cards()
```

**Interaction Guidelines**:
- Color-coded metrics
- Trend indicators
- Click to view details
- Responsive layout

### Activity Feed (`components/activity_feed.py`)

**Purpose**: Display recent user activities

**Props**: None

**Methods**:
- `activity_feed()`: Renders the activity feed

**Usage Example**:
```python
from components.activity_feed import activity_feed

# Display activity feed
activity_feed()
```

**Interaction Guidelines**:
- Timeline layout
- Expandable details
- Load more functionality
- Activity type icons

### Quick Actions (`components/quick_actions.py`)

**Purpose**: Quick access to common actions

**Props**: None

**Methods**:
- `quick_action_buttons()`: Renders quick action buttons

**Usage Example**:
```python
from components.quick_actions import quick_action_buttons

# Display quick actions
quick_action_buttons()
```

**Interaction Guidelines**:
- Grid layout
- Icon-based actions
- Loading states
- Consistent styling

### Health Insights Widget (`components/health_insights.py`)

**Purpose**: Display personalized health insights

**Props**: None

**Methods**:
- `health_insights_widget()`: Renders health insights widget
- `health_insights_dashboard()`: Renders full insights dashboard

**Usage Example**:
```python
from components.health_insights import health_insights_widget

# Display health insights
health_insights_widget()
```

---

## Health Profile Components

### User Profile (`pages/profile.py`)

**Purpose**: User profile management

**Props**: None

**Methods**:
- `profile_page()`: Renders the profile page

**Usage Example**:
```python
from pages.profile import profile_page

# Show profile page
profile_page()
```

**Interaction Guidelines**:
- Editable fields
- Profile picture upload
- Save/cancel functionality
- Form validation

---

## Chat Components

### Enhanced Chat Interface (`components/enhanced_chat.py`)

**Purpose**: Main chat interface with AI assistant

**Props**: None

**Methods**:
- `SimpleChatInterface.setup_page()`: Sets up the chat page
- `SimpleChatInterface.render_sidebar()`: Renders the sidebar

**Usage Example**:
```python
from components.enhanced_chat import SimpleChatInterface

chat_interface = SimpleChatInterface()
chat_interface.setup_page()
profile_data = chat_interface.render_sidebar()
```

### Chat Analytics (`components/chat_analytics.py`)

**Purpose**: Chat conversation analytics

**Props**: None

**Methods**:
- `chat_analytics()`: Renders chat analytics

**Usage Example**:
```python
from components.chat_analytics import chat_analytics

# Display chat analytics
chat_analytics()
```

### Chat History (`pages/chat_history.py`)

**Purpose**: Chat history management

**Props**: None

**Methods**:
- `chat_history_page()`: Renders chat history page

**Usage Example**:
```python
from pages.chat_history import chat_history_page

# Show chat history
chat_history_page()
```

---

## Metrics Components

### Health Metrics (`pages/health_metrics.py`)

**Purpose**: Health metrics input and visualization

**Props**: None

**Methods**:
- `health_metrics_page()`: Renders health metrics page

**Usage Example**:
```python
from pages.health_metrics import health_metrics_page

# Show health metrics page
health_metrics_page()
```

### Metrics Visualization (`components/metrics_visualization.py`)

**Purpose**: Interactive charts for health metrics

**Props**: None

**Methods**:
- `metrics_visualization()`: Renders metrics visualization

**Usage Example**:
```python
from components.metrics_visualization import metrics_visualization

# Display metrics visualization
metrics_visualization()
```

### Health Goals (`components/health_goals.py`)

**Purpose**: Health goals tracking

**Props**: None

**Methods**:
- `health_goals()`: Renders health goals

**Usage Example**:
```python
from components.health_goals import health_goals

# Display health goals
health_goals()
```

### Metrics Summary (`components/metrics_summary.py`)

**Purpose**: Summary cards for health metrics

**Props**: None

**Methods**:
- `metrics_summary_cards()`: Renders metrics summary cards

**Usage Example**:
```python
from components.metrics_summary import metrics_summary_cards

# Display metrics summary
metrics_summary_cards()
```

---

## Reports Components

### Reports Page (`pages/reports.py`)

**Purpose**: Report generation and management

**Props**: None

**Methods**:
- `reports_page()`: Renders reports page

**Usage Example**:
```python
from pages.reports import reports_page

# Show reports page
reports_page()
```

---

## Settings Components

### Settings Page (`pages/settings.py`)

**Purpose**: Application settings management

**Props**: None

**Methods**:
- `settings_page()`: Renders settings page

**Usage Example**:
```python
from pages.settings import settings_page

# Show settings page
settings_page()
```

---

## Interactive Components

### Loading and Modals (`components/loading_and_modals.py`)

**Purpose**: Loading states and modal components

**Props**: Various for different components

**Methods**:
- `loading_spinner(message)`: Shows loading spinner
- `skeleton_loading()`: Shows skeleton loading
- `modal_component(title, content, type)`: Shows modal
- `confirmation_modal(title, message)`: Shows confirmation modal

**Usage Example**:
```python
from components.loading_and_modals import loading_spinner, modal_component

# Show loading spinner
with loading_spinner("Loading data..."):
    # Perform operation
    pass

# Show modal
modal_component("Success", "Operation completed!", "success")
```

### Interactive Tables (`components/interactive_tables.py`)

**Purpose**: Advanced data table components

**Props**: Various for different table types

**Methods**:
- `sortable_table(df)`: Creates sortable table
- `paginated_table(df)`: Creates paginated table
- `selectable_table(df)`: Creates selectable table
- `filterable_table(df)`: Creates filterable table

**Usage Example**:
```python
from components.interactive_tables import sortable_table, generate_sample_data

# Create and display sortable table
df = generate_sample_data()
sortable_table(df)
```

---

## Performance Components

### Performance Optimization (`components/performance_optimization.py`)

**Purpose**: Performance monitoring and optimization tools

**Props**: Various for different components

**Methods**:
- `performance_dashboard()`: Main performance dashboard
- `lazy_loading_list(items, page_size)`: Lazy loading list
- `memoized_data_processing()`: Memoized data processing
- `bundle_size_analyzer()`: Bundle size analysis

**Usage Example**:
```python
from components.performance_optimization import performance_dashboard

# Show performance dashboard
performance_dashboard()
```

---

## Session Management

### Session Management (`components/session_management.py`)

**Purpose**: User session management

**Props**: None

**Methods**:
- `session_timeout_warning()`: Shows session timeout warning
- `logout_confirmation()`: Shows logout confirmation

**Usage Example**:
```python
from components.session_management import session_timeout_warning

# Show session timeout warning
session_timeout_warning()
```

---

## Component Interaction Guidelines

### General Guidelines
1. **Consistent Styling**: All components use the same design system
2. **Responsive Design**: Components adapt to different screen sizes
3. **Accessibility**: All components support keyboard navigation and screen readers
4. **Loading States**: Components show appropriate loading states
5. **Error Handling**: Components handle errors gracefully

### State Management
1. **Session State**: Use `st.session_state` for component state
2. **Data Persistence**: Store important data in session state
3. **Cache Management**: Use memoization for expensive operations
4. **State Synchronization**: Keep component states synchronized

### Performance Best Practices
1. **Lazy Loading**: Use lazy loading for large datasets
2. **Memoization**: Cache expensive calculations
3. **Optimized Rendering**: Minimize unnecessary re-renders
4. **Bundle Optimization**: Keep component bundles small

### Testing Guidelines
1. **Unit Tests**: Write tests for all component functions
2. **Integration Tests**: Test component interactions
3. **Mock Dependencies**: Mock external dependencies in tests
4. **Edge Cases**: Test error conditions and edge cases

---

## Style Guide

### Color Palette
- **Primary**: #1f77b4 (Blue)
- **Secondary**: #ff7f0e (Orange)
- **Success**: #2ca02c (Green)
- **Warning**: #d62728 (Red)
- **Info**: #17a2b8 (Cyan)

### Typography
- **Headers**: Use `st.markdown()` with appropriate heading levels
- **Body Text**: Use `st.write()` for regular text
- **Code**: Use `st.code()` for code blocks

### Layout
- **Grid System**: Use 12-column responsive grid
- **Spacing**: Consistent padding and margins
- **Alignment**: Left-align text, center-align buttons

### Icons
- **Navigation**: Use consistent icon set
- **Actions**: Use descriptive icons for buttons
- **Status**: Use color-coded icons for status indicators

---

## Troubleshooting

### Common Issues
1. **Component Not Rendering**: Check if all required props are provided
2. **State Not Updating**: Verify session state is properly initialized
3. **Performance Issues**: Use performance monitoring tools
4. **Styling Issues**: Check CSS class names and theme variables

### Debug Tips
1. **Use `st.write()`** to debug component state
2. **Check browser console** for JavaScript errors
3. **Monitor network requests** for API issues
4. **Use performance dashboard** for optimization

---

## Version History

### v1.0.0 (Current)
- Initial component library
- Basic dashboard functionality
- Authentication system
- Health metrics tracking
- Chat interface
- Performance optimization tools

### Future Enhancements
- Advanced analytics
- Machine learning integration
- Mobile app components
- Real-time collaboration
- Advanced customization options 