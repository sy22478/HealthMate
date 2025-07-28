#!/bin/bash

# HealthMate Test Runner Script
# This script provides various options for running tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "HealthMate Test Runner"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  unit              Run unit tests only"
    echo "  integration       Run integration tests only"
    echo "  all               Run all tests"
    echo "  coverage          Run tests with coverage report"
    echo "  docker            Run tests in Docker containers"
    echo "  clean             Clean up test artifacts"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 unit           # Run unit tests"
    echo "  $0 integration    # Run integration tests"
    echo "  $0 coverage       # Run all tests with coverage"
    echo "  $0 docker         # Run tests in Docker"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    python -m pytest tests/ -v -m "unit" --tb=short
    print_success "Unit tests completed"
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    python -m pytest tests/ -v -m "integration" --tb=short
    print_success "Integration tests completed"
}

# Function to run all tests
run_all_tests() {
    print_status "Running all tests..."
    python -m pytest tests/ -v --tb=short
    print_success "All tests completed"
}

# Function to run tests with coverage
run_coverage_tests() {
    print_status "Running tests with coverage..."
    python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml
    print_success "Coverage tests completed"
    print_status "Coverage report generated in htmlcov/ directory"
}

# Function to run tests in Docker
run_docker_tests() {
    print_status "Running tests in Docker containers..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build and run test containers
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    
    print_success "Docker tests completed"
}

# Function to clean up test artifacts
clean_test_artifacts() {
    print_status "Cleaning up test artifacts..."
    
    # Remove test database
    if [ -f "test.db" ]; then
        rm test.db
        print_status "Removed test.db"
    fi
    
    # Remove coverage reports
    if [ -d "htmlcov" ]; then
        rm -rf htmlcov
        print_status "Removed htmlcov directory"
    fi
    
    if [ -f "coverage.xml" ]; then
        rm coverage.xml
        print_status "Removed coverage.xml"
    fi
    
    # Remove pytest cache
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache
        print_status "Removed .pytest_cache directory"
    fi
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_status "Removed __pycache__ directories"
    
    print_success "Cleanup completed"
}

# Function to setup test environment
setup_test_env() {
    print_status "Setting up test environment..."
    
    # Create test database if it doesn't exist
    if [ ! -f "test.db" ]; then
        print_status "Creating test database..."
        python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
    fi
    
    # Install test dependencies if needed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "Installing test dependencies..."
        pip install pytest pytest-cov pytest-xdist pytest-asyncio httpx coverage
    fi
    
    print_success "Test environment setup completed"
}

# Main script logic
main() {
    case "${1:-help}" in
        "unit")
            setup_test_env
            run_unit_tests
            ;;
        "integration")
            setup_test_env
            run_integration_tests
            ;;
        "all")
            setup_test_env
            run_all_tests
            ;;
        "coverage")
            setup_test_env
            run_coverage_tests
            ;;
        "docker")
            run_docker_tests
            ;;
        "clean")
            clean_test_artifacts
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 