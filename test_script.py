#!/usr/bin/env python3
"""
Test script for the AI Digital Worker Factory
Demonstrates how to submit a job and check status
"""

import json
import base64
import requests
import time
import zipfile
import io

# Configuration - update with your API Gateway URL
API_BASE_URL = "https://your-api-gateway-url"

def create_sample_zip():
    """Create a sample ZIP file with NopCommerce-like code"""
    
    # Sample C# code for a shopping cart
    sample_code = '''
using System;
using System.Collections.Generic;

namespace NopCommerce.Core.Domain.Orders
{
    public class ShoppingCartItem
    {
        public int Id { get; set; }
        public string ProductId { get; set; }
        public int Quantity { get; set; }
        public decimal Price { get; set; }
        public DateTime CreatedOnUtc { get; set; }
        
        public decimal GetTotalPrice()
        {
            return Quantity * Price;
        }
    }
    
    public class ShoppingCartService
    {
        private readonly List<ShoppingCartItem> _items;
        
        public ShoppingCartService()
        {
            _items = new List<ShoppingCartItem>();
        }
        
        public void AddItem(string productId, int quantity, decimal price)
        {
            var item = new ShoppingCartItem
            {
                ProductId = productId,
                Quantity = quantity,
                Price = price,
                CreatedOnUtc = DateTime.UtcNow
            };
            
            _items.Add(item);
        }
        
        public decimal GetTotalAmount()
        {
            decimal total = 0;
            foreach (var item in _items)
            {
                total += item.GetTotalPrice();
            }
            return total;
        }
        
        public void RemoveItem(int itemId)
        {
            _items.RemoveAll(x => x.Id == itemId);
        }
    }
}
'''
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('ShoppingCartService.cs', sample_code)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def submit_job():
    """Submit a document generation job"""
    
    # Create sample ZIP
    zip_content = create_sample_zip()
    zip_base64 = base64.b64encode(zip_content).decode('utf-8')
    
    # Feature descriptor
    descriptor = {
        "moduleName": "ShoppingCart",
        "version": "1.0",
        "features": [
            {
                "id": "cart-001",
                "description": "Add items to shopping cart with product ID, quantity, and price"
            },
            {
                "id": "cart-002", 
                "description": "Calculate total amount of all items in cart"
            },
            {
                "id": "cart-003",
                "description": "Remove items from shopping cart by item ID"
            }
        ]
    }
    
    # Submit job
    payload = {
        "archive": zip_base64,
        "descriptor": descriptor
    }
    
    print("Submitting document generation job...")
    response = requests.post(
        f"{API_BASE_URL}/generate-spec",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 202:
        job_data = response.json()
        job_id = job_data['jobId']
        print(f"Job submitted successfully! Job ID: {job_id}")
        return job_id
    else:
        print(f"Error submitting job: {response.status_code} - {response.text}")
        return None

def check_job_status(job_id):
    """Check the status of a job"""
    
    print(f"Checking status for job {job_id}...")
    response = requests.get(f"{API_BASE_URL}/job-status/{job_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error checking status: {response.status_code} - {response.text}")
        return None

def wait_for_completion(job_id, max_wait_time=300):
    """Wait for job completion with polling"""
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status_data = check_job_status(job_id)
        
        if status_data:
            status = status_data['status']
            print(f"Job status: {status}")
            
            if status == 'Succeeded':
                download_url = status_data.get('downloadUrl')
                print(f"Job completed successfully!")
                print(f"Download URL: {download_url}")
                return True
            elif status == 'Failed':
                error_msg = status_data.get('errorMessage', 'Unknown error')
                print(f"Job failed: {error_msg}")
                return False
        
        print("Waiting 10 seconds before next check...")
        time.sleep(10)
    
    print("Timeout waiting for job completion")
    return False

def main():
    """Main test function"""
    
    print("AI Digital Worker Factory - Test Script")
    print("=" * 50)
    
    # Update API URL
    global API_BASE_URL
    api_url = input(f"Enter API Gateway URL (or press Enter for default): ").strip()
    if api_url:
        API_BASE_URL = api_url.rstrip('/')
    
    print(f"Using API URL: {API_BASE_URL}")
    
    # Submit job
    job_id = submit_job()
    if not job_id:
        return
    
    # Wait for completion
    success = wait_for_completion(job_id)
    
    if success:
        print("\nTest completed successfully!")
        print("The generated specification document is ready for download.")
    else:
        print("\nTest failed or timed out.")

if __name__ == "__main__":
    main()