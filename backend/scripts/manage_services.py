#!/usr/bin/env python3
"""
Service management utility for Faithful Finances backend.

This script provides commands to manage external services, run health checks,
and perform maintenance operations.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.redis import get_redis_client, CacheService, SessionService, RateLimiter
from src.services.stripe import get_stripe_client, SubscriptionService
from src.services.plaid import get_plaid_client
from src.services.background import TaskScheduler


async def health_check():
    """Run comprehensive health check on all services."""
    print("🏥 Running health checks on all services...\n")
    
    services = {}
    
    # Redis health check
    try:
        redis_client = await get_redis_client()
        services["redis"] = await redis_client.health_check()
    except Exception as e:
        services["redis"] = {"status": "error", "error": str(e)}
    
    # Stripe health check
    try:
        stripe_client = get_stripe_client()
        services["stripe"] = await stripe_client.health_check()
    except Exception as e:
        services["stripe"] = {"status": "error", "error": str(e)}
    
    # Plaid health check
    try:
        plaid_client = get_plaid_client()
        services["plaid"] = await plaid_client.health_check()
    except Exception as e:
        services["plaid"] = {"status": "error", "error": str(e)}
    
    # Celery health check
    try:
        scheduler = TaskScheduler()
        services["celery"] = await scheduler.health_check()
    except Exception as e:
        services["celery"] = {"status": "error", "error": str(e)}
    
    # Print results
    for service, health in services.items():
        status = health.get("status", "unknown")
        emoji = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "⚠️"
        print(f"{emoji} {service.upper()}: {status}")
        
        if "details" in health:
            for key, value in health["details"].items():
                print(f"   {key}: {value}")
        
        if "error" in health:
            print(f"   Error: {health['error']}")
        
        print()
    
    # Overall status
    all_healthy = all(h.get("status") == "healthy" for h in services.values())
    overall_emoji = "✅" if all_healthy else "❌"
    print(f"{overall_emoji} Overall Status: {'HEALTHY' if all_healthy else 'ISSUES DETECTED'}")
    
    return services


async def redis_operations(action: str, **kwargs):
    """Perform Redis operations."""
    redis_client = await get_redis_client()
    cache_service = CacheService()
    session_service = SessionService()
    
    if action == "stats":
        print("📊 Redis Statistics:\n")
        
        # Basic stats
        info = await redis_client.client.info()
        print(f"Connected clients: {info.get('connected_clients', 'N/A')}")
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")
        print(f"Keys: {info.get('db0', {}).get('keys', 'N/A')}")
        print(f"Uptime: {info.get('uptime_in_seconds', 'N/A')} seconds")
        
    elif action == "flush":
        confirm = input("⚠️  This will delete ALL Redis data. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            await redis_client.flushdb()
            print("✅ Redis database flushed")
        else:
            print("❌ Operation cancelled")
    
    elif action == "cleanup-sessions":
        print("🧹 Cleaning up expired sessions...")
        count = await session_service.cleanup_expired_sessions()
        print(f"✅ Cleaned {count} expired sessions")
    
    elif action == "test":
        print("🧪 Testing Redis operations...")
        
        # Test basic operations
        await redis_client.set("test_key", "test_value", ttl=60)
        value = await redis_client.get("test_key")
        print(f"Basic operation: {'✅' if value == 'test_value' else '❌'}")
        
        # Test cache
        await cache_service.set("test_tenant", "cache_test", {"test": True}, ttl=60)
        cached = await cache_service.get("test_tenant", "cache_test")
        print(f"Cache operation: {'✅' if cached and cached.get('test') else '❌'}")
        
        # Cleanup
        await redis_client.delete("test_key")
        await cache_service.delete("test_tenant", "cache_test")
        print("✅ Test cleanup completed")


async def stripe_operations(action: str, **kwargs):
    """Perform Stripe operations."""
    stripe_client = get_stripe_client()
    
    if action == "plans":
        print("💳 Available Stripe Plans:\n")
        prices = await stripe_client.list_prices(active=True)
        
        for price in prices.data:
            print(f"ID: {price.id}")
            print(f"Amount: {price.unit_amount / 100} {price.currency.upper()}")
            print(f"Interval: {price.recurring.interval if price.recurring else 'one-time'}")
            print(f"Active: {price.active}")
            print("-" * 40)
    
    elif action == "webhooks":
        print("🔗 Stripe Webhook Configuration:")
        
        from src.services.stripe import WebhookService
        webhook_service = WebhookService()
        
        config = await webhook_service.validate_webhook_configuration()
        print(f"Configuration valid: {'✅' if config['valid'] else '❌'}")
        
        if config.get('errors'):
            for error in config['errors']:
                print(f"❌ {error}")
        
        print(f"Registered handlers: {config['details'].get('registered_handlers', 0)}")


async def plaid_operations(action: str, **kwargs):
    """Perform Plaid operations."""
    plaid_client = get_plaid_client()
    
    if action == "institutions":
        print("🏦 Plaid Institutions (sample):\n")
        
        institutions = await plaid_client.get_institutions(count=10)
        
        for institution in institutions.get("institutions", [])[:5]:
            print(f"Name: {institution.get('name', 'N/A')}")
            print(f"ID: {institution.get('institution_id', 'N/A')}")
            print(f"Country: {', '.join(institution.get('country_codes', []))}")
            print(f"Products: {', '.join(institution.get('products', []))}")
            print("-" * 40)
    
    elif action == "webhooks":
        print("🔗 Plaid Webhook Configuration:")
        
        from src.services.plaid import WebhookService
        webhook_service = WebhookService()
        
        config = await webhook_service.validate_webhook_configuration()
        print(f"Configuration valid: {'✅' if config['valid'] else '❌'}")
        
        if config.get('errors'):
            for error in config['errors']:
                print(f"❌ {error}")
        
        supported = config['details'].get('supported_events', {})
        for event_type, events in supported.items():
            print(f"{event_type}: {len(events)} events")


async def celery_operations(action: str, **kwargs):
    """Perform Celery operations."""
    scheduler = TaskScheduler()
    
    if action == "workers":
        print("👷 Celery Workers:\n")
        
        stats = await scheduler.get_worker_stats()
        
        if not stats:
            print("❌ No active workers found")
            return
        
        for worker, worker_data in stats.items():
            print(f"Worker: {worker}")
            print(f"Active tasks: {worker_data['active_tasks']}")
            print(f"Reserved tasks: {worker_data['reserved_tasks']}")
            
            worker_stats = worker_data.get('stats', {})
            if worker_stats:
                print(f"Total tasks: {worker_stats.get('total', 'N/A')}")
                print(f"Pool processes: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
            
            print("-" * 40)
    
    elif action == "tasks":
        print("📋 Active Tasks:\n")
        
        tasks = await scheduler.get_active_tasks()
        
        if not tasks:
            print("✅ No active tasks")
            return
        
        for task in tasks:
            print(f"Task: {task['task_name']}")
            print(f"ID: {task['task_id']}")
            print(f"Worker: {task['worker']}")
            print(f"Started: {task.get('time_start', 'N/A')}")
            print("-" * 40)
    
    elif action == "schedule":
        print("⏰ Scheduled Tasks:\n")
        
        scheduled = await scheduler.get_scheduled_tasks()
        
        for task_name, task_info in scheduled.items():
            print(f"Name: {task_name}")
            print(f"Task: {task_info['task']}")
            print(f"Schedule: {task_info['schedule']}")
            print(f"Args: {task_info.get('args', [])}")
            print("-" * 40)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage Faithful Finances external services")
    parser.add_argument("command", choices=[
        "health", "redis", "stripe", "plaid", "celery"
    ], help="Command to run")
    
    parser.add_argument("--action", help="Specific action to perform")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    try:
        if args.command == "health":
            result = await health_check()
            if args.json:
                print(json.dumps(result, indent=2))
        
        elif args.command == "redis":
            action = args.action or "stats"
            await redis_operations(action)
        
        elif args.command == "stripe":
            action = args.action or "plans"
            await stripe_operations(action)
        
        elif args.command == "plaid":
            action = args.action or "institutions"
            await plaid_operations(action)
        
        elif args.command == "celery":
            action = args.action or "workers"
            await celery_operations(action)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())