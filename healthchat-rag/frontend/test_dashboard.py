"""
HealthMate Dashboard Test Script
Test the dashboard functionality and API integration
"""
import requests
import json
import os
from datetime import datetime

class DashboardTester:
    """Test class for HealthMate Dashboard"""
    
    def __init__(self):
        self.base_url = os.getenv("HEALTHMATE_API_URL", "https://healthmate-production.up.railway.app")
        self.session = requests.Session()
        self.auth_token = None
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health/debug")
            if response.status_code == 200:
                print("✅ API connectivity test passed")
                return True
            else:
                print(f"❌ API connectivity test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API connectivity test failed: {str(e)}")
            return False
    
    def test_authentication(self, email: str, password: str) -> bool:
        """Test authentication endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                print("✅ Authentication test passed")
                return True
            else:
                print(f"❌ Authentication test failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")
            return False
    
    def test_dashboard_endpoints(self) -> bool:
        """Test dashboard-related endpoints"""
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        endpoints = [
            "/advanced-analytics/dashboard",
            "/analytics/health-score",
            "/health-data/",
            "/visualization/available-charts"
        ]
        
        success_count = 0
        total_endpoints = len(endpoints)
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✅ {endpoint} - OK")
                    success_count += 1
                else:
                    print(f"❌ {endpoint} - Failed ({response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {str(e)}")
        
        print(f"\n📊 Endpoint Test Results: {success_count}/{total_endpoints} passed")
        return success_count == total_endpoints
    
    def test_visualization_endpoints(self) -> bool:
        """Test visualization endpoints"""
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        chart_types = [
            "health_trends",
            "symptom_distribution", 
            "medication_adherence",
            "data_completeness"
        ]
        
        success_count = 0
        total_charts = len(chart_types)
        
        for chart_type in chart_types:
            try:
                response = self.session.get(
                    f"{self.base_url}/visualization/chart/{chart_type}",
                    params={"days": 30}
                )
                if response.status_code == 200:
                    print(f"✅ {chart_type} chart - OK")
                    success_count += 1
                else:
                    print(f"❌ {chart_type} chart - Failed ({response.status_code})")
            except Exception as e:
                print(f"❌ {chart_type} chart - Error: {str(e)}")
        
        print(f"\n📊 Visualization Test Results: {success_count}/{total_charts} passed")
        return success_count == total_charts
    
    def test_data_export(self) -> bool:
        """Test data export functionality"""
        if not self.auth_token:
            print("❌ No authentication token available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/advanced-analytics/export/analytics",
                params={"format": "json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    print("✅ Data export test passed")
                    return True
                else:
                    print("❌ Data export test failed: Invalid response format")
                    return False
            else:
                print(f"❌ Data export test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Data export test failed: {str(e)}")
            return False
    
    def run_full_test_suite(self, email: str = None, password: str = None) -> bool:
        """Run complete test suite"""
        print("🧪 HealthMate Dashboard Test Suite")
        print("=" * 50)
        
        # Test 1: API Connectivity
        print("\n1. Testing API Connectivity...")
        if not self.test_api_connectivity():
            return False
        
        # Test 2: Authentication (if credentials provided)
        if email and password:
            print("\n2. Testing Authentication...")
            if not self.test_authentication(email, password):
                print("⚠️  Authentication failed, but continuing with public endpoints...")
            else:
                # Test 3: Dashboard Endpoints (requires authentication)
                print("\n3. Testing Dashboard Endpoints...")
                self.test_dashboard_endpoints()
                
                # Test 4: Visualization Endpoints (requires authentication)
                print("\n4. Testing Visualization Endpoints...")
                self.test_visualization_endpoints()
                
                # Test 5: Data Export (requires authentication)
                print("\n5. Testing Data Export...")
                self.test_data_export()
        else:
            print("\n2. Skipping Authentication Test (no credentials provided)")
            print("   To test authenticated endpoints, provide email and password")
        
        # Test 6: Public Endpoints
        print("\n6. Testing Public Endpoints...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health endpoint - OK")
            else:
                print(f"❌ Health endpoint - Failed ({response.status_code})")
        except Exception as e:
            print(f"❌ Health endpoint - Error: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Test suite completed!")
        print("\n📋 Next Steps:")
        print("1. Start the dashboard: ./start_dashboard.sh")
        print("2. Open browser: http://localhost:8501")
        print("3. Login with your credentials")
        print("4. Explore the dashboard features")
        
        return True

def main():
    """Main test function"""
    tester = DashboardTester()
    
    # Get credentials from environment or user input
    email = os.getenv("HEALTHMATE_EMAIL")
    password = os.getenv("HEALTHMATE_PASSWORD")
    
    if not email:
        email = input("Enter HealthMate email (or press Enter to skip auth tests): ").strip()
    
    if not password and email:
        password = input("Enter HealthMate password: ").strip()
    
    # Run test suite
    tester.run_full_test_suite(email if email else None, password if password else None)

if __name__ == "__main__":
    main() 