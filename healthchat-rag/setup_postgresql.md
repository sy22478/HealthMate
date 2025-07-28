# PostgreSQL Setup Guide for HealthMate

## 🗄️ **Phase 1.2.1: PostgreSQL Setup**

### **Step 1: Add PostgreSQL Service in Railway**

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Select your project: `pleasant-eagerness`

2. **Add PostgreSQL Service**
   - Click "New Service"
   - Select "PostgreSQL" from the template gallery
   - Wait for the service to provision (usually 1-2 minutes)

3. **Get Connection Details**
   - Click on the PostgreSQL service
   - Go to "Connect" tab
   - Copy the connection string

### **Step 2: Configure Environment Variables**

1. **Add Database URL to Railway**
   - Go to your main service (HealthMate)
   - Click "Variables" tab
   - Add new variable:
     - **Key**: `DATABASE_URL`
     - **Value**: `postgresql://your_username:your_password@your_host:your_port/your_database`  # pragma: allowlist secret
   - Copy the connection string from PostgreSQL service

2. **Add PostgreSQL URL for Alembic**
   - Add another variable:
     - **Key**: `POSTGRES_URI`
     - **Value**: Same as DATABASE_URL

### **Step 3: Run Database Migrations**

1. **Create Initial Migration**
   ```bash
   alembic revision --autogenerate -m "Initial database setup"
   ```

2. **Run Migration**
   ```bash
   alembic upgrade head
   ```

3. **Verify Tables Created**
   ```bash
   alembic current
   ```

### **Step 4: Test Database Connection**

1. **Test Connection in App**
   - Deploy the app
   - Check logs for database connection success
   - Test registration endpoint

2. **Verify Tables**
   - Connect to PostgreSQL database
   - List all tables: `\dt`
   - Should see: users, health_data, conversations, etc.

### **Step 5: Backup and Monitoring**

1. **Set Up Database Backups**
   - Railway provides automatic backups
   - Check backup settings in PostgreSQL service

2. **Monitor Database Performance**
   - Check Railway metrics
   - Monitor connection pool usage
   - Set up alerts for high usage

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Connection Failed**
   - Check DATABASE_URL format
   - Verify SSL settings
   - Check firewall rules

2. **Migration Errors**
   - Check model imports in env.py
   - Verify Base metadata
   - Check for syntax errors in models

3. **Permission Errors**
   - Check database user permissions
   - Verify connection string credentials

### **Useful Commands:**

```bash
# Check current migration
alembic current

# List all migrations
alembic history

# Downgrade to previous migration
alembic downgrade -1

# Upgrade to latest migration
alembic upgrade head

# Show migration info
alembic show <revision>
```

## 📊 **Database Schema Overview**

### **Core Tables:**
- `users` - User accounts and profiles
- `health_data` - Health metrics and measurements
- `conversations` - Chat history with AI
- `symptom_logs` - User symptom tracking
- `medication_logs` - Medication tracking
- `notifications` - User notifications

### **Enhanced Tables:**
- `user_health_profiles` - Detailed health profiles
- `user_preferences` - User preferences
- `conversation_history` - Enhanced chat history
- `health_goals` - User health goals
- `health_alerts` - Health alerts and warnings

## 🚀 **Next Steps**

After PostgreSQL setup:
1. **Test User Registration** - Verify database operations
2. **Test Health Data Storage** - Verify data persistence
3. **Test AI Chat** - Verify conversation storage
4. **Set Up Monitoring** - Monitor database performance
5. **Create Backups** - Set up automated backups 