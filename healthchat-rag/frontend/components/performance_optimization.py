import streamlit as st
import time
import functools
from typing import List, Dict, Any, Callable
import pandas as pd
import numpy as np

# Performance monitoring utilities
def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Store performance metrics in session state
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
        
        st.session_state.performance_metrics[func.__name__] = {
            'execution_time': execution_time,
            'timestamp': time.time(),
            'calls': st.session_state.performance_metrics.get(func.__name__, {}).get('calls', 0) + 1
        }
        
        return result
    return wrapper

def show_performance_metrics():
    """Display performance metrics dashboard"""
    if 'performance_metrics' not in st.session_state:
        st.info("No performance metrics available yet.")
        return
    
    st.markdown("### Performance Metrics Dashboard")
    
    metrics = st.session_state.performance_metrics
    if not metrics:
        st.info("No performance data collected yet.")
        return
    
    # Create performance summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_calls = sum(m['calls'] for m in metrics.values())
        st.metric("Total Function Calls", total_calls)
    
    with col2:
        avg_time = np.mean([m['execution_time'] for m in metrics.values()])
        st.metric("Average Execution Time", f"{avg_time:.4f}s")
    
    with col3:
        max_time = max([m['execution_time'] for m in metrics.values()])
        st.metric("Slowest Function", f"{max_time:.4f}s")
    
    # Performance table
    st.markdown("#### Function Performance Details")
    performance_data = []
    for func_name, data in metrics.items():
        performance_data.append({
            'Function': func_name,
            'Calls': data['calls'],
            'Avg Time (s)': f"{data['execution_time']:.4f}",
            'Total Time (s)': f"{data['execution_time'] * data['calls']:.4f}"
        })
    
    if performance_data:
        df = pd.DataFrame(performance_data)
        st.dataframe(df, use_container_width=True)

# Lazy loading components
class LazyList:
    """Lazy loading list component for large datasets"""
    
    def __init__(self, items: List[Any], page_size: int = 20):
        self.items = items
        self.page_size = page_size
        self.current_page = 0
        
    def get_current_page(self) -> List[Any]:
        """Get current page of items"""
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        return self.items[start_idx:end_idx]
    
    def has_next_page(self) -> bool:
        """Check if there are more pages"""
        return (self.current_page + 1) * self.page_size < len(self.items)
    
    def has_previous_page(self) -> bool:
        """Check if there are previous pages"""
        return self.current_page > 0
    
    def next_page(self):
        """Move to next page"""
        if self.has_next_page():
            self.current_page += 1
    
    def previous_page(self):
        """Move to previous page"""
        if self.has_previous_page():
            self.current_page -= 1

def lazy_loading_list(items: List[Any], page_size: int = 20, title: str = "Lazy Loading List"):
    """Display a lazy loading list with pagination controls"""
    st.markdown(f"### {title}")
    
    if not items:
        st.info("No items to display.")
        return
    
    # Initialize lazy list in session state
    if 'lazy_list' not in st.session_state:
        st.session_state.lazy_list = LazyList(items, page_size)
    
    lazy_list = st.session_state.lazy_list
    
    # Display current page
    current_items = lazy_list.get_current_page()
    
    # Show items
    for i, item in enumerate(current_items):
        with st.container():
            if isinstance(item, dict):
                st.json(item)
            else:
                st.write(f"Item {lazy_list.current_page * page_size + i + 1}: {item}")
    
    # Pagination controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if st.button("← Previous", disabled=not lazy_list.has_previous_page()):
            lazy_list.previous_page()
            st.rerun()
    
    with col2:
        st.write(f"Page {lazy_list.current_page + 1}")
    
    with col3:
        if st.button("Next →", disabled=not lazy_list.has_next_page()):
            lazy_list.next_page()
            st.rerun()
    
    with col4:
        st.write(f"Showing {len(current_items)} of {len(items)} items")

# Memoization utilities
@performance_monitor
def expensive_calculation(data: List[float], complexity: int = 1000) -> Dict[str, float]:
    """Simulate an expensive calculation with memoization"""
    # Create a cache key based on input parameters
    cache_key = f"calc_{hash(tuple(data))}_{complexity}"
    
    # Check if result is already cached
    if 'calculation_cache' not in st.session_state:
        st.session_state.calculation_cache = {}
    
    if cache_key in st.session_state.calculation_cache:
        st.info("Using cached result!")
        return st.session_state.calculation_cache[cache_key]
    
    # Simulate expensive calculation
    st.info("Performing expensive calculation...")
    time.sleep(0.5)  # Simulate processing time
    
    # Perform calculation
    result = {
        'mean': np.mean(data),
        'std': np.std(data),
        'min': np.min(data),
        'max': np.max(data),
        'sum': np.sum(data),
        'complexity_factor': complexity
    }
    
    # Cache the result
    st.session_state.calculation_cache[cache_key] = result
    return result

def memoized_data_processing():
    """Demonstrate memoized data processing"""
    st.markdown("### Memoized Data Processing")
    
    # Input controls
    col1, col2 = st.columns(2)
    
    with col1:
        data_size = st.slider("Data Size", 100, 10000, 1000, step=100)
        complexity = st.slider("Calculation Complexity", 100, 5000, 1000, step=100)
    
    with col2:
        if st.button("Generate New Data"):
            # Generate random data
            data = np.random.normal(0, 1, data_size).tolist()
            st.session_state.current_data = data
            st.session_state.calculation_cache = {}  # Clear cache for new data
            st.success("New data generated!")
    
    # Use existing data or generate default
    if 'current_data' not in st.session_state:
        st.session_state.current_data = np.random.normal(0, 1, 1000).tolist()
    
    data = st.session_state.current_data
    
    # Display data info
    st.write(f"**Data Size:** {len(data)} points")
    st.write(f"**Data Range:** {min(data):.2f} to {max(data):.2f}")
    
    # Perform calculation
    if st.button("Run Expensive Calculation"):
        result = expensive_calculation(data, complexity)
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Mean", f"{result['mean']:.4f}")
            st.metric("Standard Deviation", f"{result['std']:.4f}")
        
        with col2:
            st.metric("Minimum", f"{result['min']:.4f}")
            st.metric("Maximum", f"{result['max']:.4f}")
        
        with col3:
            st.metric("Sum", f"{result['sum']:.4f}")
            st.metric("Complexity", result['complexity_factor'])
    
    # Show cache info
    if 'calculation_cache' in st.session_state:
        cache_size = len(st.session_state.calculation_cache)
        st.info(f"Cache contains {cache_size} cached calculations")
        
        if st.button("Clear Cache"):
            st.session_state.calculation_cache = {}
            st.success("Cache cleared!")

# Image optimization utilities
def optimize_image_display(image_path: str, max_width: int = 800, quality: int = 85):
    """Optimize image display with size and quality controls"""
    st.markdown("### Image Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Original Image")
        st.image(image_path, caption="Original Image", use_column_width=True)
    
    with col2:
        st.markdown("#### Optimized Display")
        # In a real implementation, this would resize and compress the image
        st.image(image_path, caption="Optimized Image", use_column_width=True)
    
    # Optimization controls
    st.markdown("#### Optimization Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input("Max Width (px)", min_value=100, max_value=2000, value=max_width, step=50)
    
    with col2:
        st.slider("Quality (%)", min_value=10, max_value=100, value=quality, step=5)
    
    with col3:
        st.selectbox("Format", ["JPEG", "PNG", "WebP"])

# Bundle size optimization
def bundle_size_analyzer():
    """Analyze and display bundle size information"""
    st.markdown("### Bundle Size Analysis")
    
    # Simulated bundle size data
    bundle_data = {
        'Component': [
            'Core Dashboard',
            'Charts & Visualizations',
            'Interactive Tables',
            'Authentication',
            'Health Metrics',
            'Chat Interface',
            'Reports Module',
            'Settings Panel'
        ],
        'Size (KB)': [45.2, 78.9, 32.1, 15.6, 28.4, 42.7, 19.3, 12.8],
        'Load Time (ms)': [120, 210, 85, 45, 95, 115, 52, 35]
    }
    
    df = pd.DataFrame(bundle_data)
    
    # Display bundle analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Component Sizes")
        st.dataframe(df, use_container_width=True)
    
    with col2:
        st.markdown("#### Performance Metrics")
        total_size = df['Size (KB)'].sum()
        total_load_time = df['Load Time (ms)'].sum()
        
        st.metric("Total Bundle Size", f"{total_size:.1f} KB")
        st.metric("Total Load Time", f"{total_load_time} ms")
        st.metric("Average Component Size", f"{total_size/len(df):.1f} KB")
    
    # Optimization suggestions
    st.markdown("#### Optimization Suggestions")
    
    large_components = df[df['Size (KB)'] > 30]
    if not large_components.empty:
        st.warning("**Large Components Detected:**")
        for _, component in large_components.iterrows():
            st.write(f"- {component['Component']}: {component['Size (KB)']:.1f} KB")
    
    slow_components = df[df['Load Time (ms)'] > 100]
    if not slow_components.empty:
        st.warning("**Slow Loading Components:**")
        for _, component in slow_components.iterrows():
            st.write(f"- {component['Component']}: {component['Load Time (ms)']} ms")

# Network performance testing
def network_performance_test():
    """Test network performance with simulated conditions"""
    st.markdown("### Network Performance Testing")
    
    # Network conditions
    network_conditions = {
        'Fast 4G': {'latency': 50, 'bandwidth': 100},
        'Slow 3G': {'latency': 300, 'bandwidth': 10},
        '2G': {'latency': 800, 'bandwidth': 2},
        'Offline': {'latency': 0, 'bandwidth': 0}
    }
    
    selected_condition = st.selectbox("Select Network Condition", list(network_conditions.keys()))
    
    if st.button("Test Performance"):
        condition = network_conditions[selected_condition]
        
        with st.spinner(f"Testing under {selected_condition} conditions..."):
            # Simulate network delay
            time.sleep(condition['latency'] / 1000)
            
            # Calculate theoretical load time
            bundle_size = 275.0  # KB (total from bundle analyzer)
            theoretical_time = (bundle_size / condition['bandwidth']) * 8  # Convert to seconds
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Network Latency", f"{condition['latency']} ms")
            
            with col2:
                st.metric("Bandwidth", f"{condition['bandwidth']} Mbps")
            
            with col3:
                st.metric("Theoretical Load Time", f"{theoretical_time:.2f}s")
            
            # Performance rating
            if theoretical_time < 2:
                st.success("✅ Excellent performance!")
            elif theoretical_time < 5:
                st.warning("⚠️ Acceptable performance")
            else:
                st.error("❌ Poor performance - optimization needed")

# Main performance dashboard
def performance_dashboard():
    """Main performance optimization dashboard"""
    st.title("Performance Optimization Dashboard")
    
    # Performance tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Performance Metrics", 
        "Lazy Loading", 
        "Memoization", 
        "Bundle Analysis", 
        "Network Testing"
    ])
    
    with tab1:
        show_performance_metrics()
    
    with tab2:
        # Generate sample data for lazy loading
        sample_data = [f"Data Item {i}" for i in range(1, 1001)]
        lazy_loading_list(sample_data, 25, "Large Dataset Lazy Loading")
    
    with tab3:
        memoized_data_processing()
    
    with tab4:
        bundle_size_analyzer()
    
    with tab5:
        network_performance_test() 