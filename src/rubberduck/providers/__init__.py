"""
LLM Provider Module System

This module automatically discovers and registers all provider implementations
in the providers/ directory. Each provider must inherit from BaseProvider.
"""

import os
import importlib
from typing import Dict, Type
from .base import BaseProvider

# Registry to hold all available providers
PROVIDERS: Dict[str, Type[BaseProvider]] = {}

def _discover_providers():
    """
    Automatically discover and register all provider modules.
    Scans the providers/ directory for Python files and imports them.
    """
    current_dir = os.path.dirname(__file__)
    
    # Get all Python files in the providers directory
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3]  # Remove .py extension
            
            # Skip base module since it's abstract
            if module_name == 'base':
                continue
                
            try:
                # Import the module
                module = importlib.import_module(f'.{module_name}', package=__name__)
                
                # Look for classes that inherit from BaseProvider
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Check if it's a class that inherits from BaseProvider (but not BaseProvider itself)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseProvider) and 
                        attr != BaseProvider):
                        
                        # Instantiate the provider
                        provider_instance = attr()
                        
                        # Register it in the PROVIDERS dict
                        PROVIDERS[provider_instance.name] = provider_instance
                        
                        print(f"Registered provider: {provider_instance.name}")
                        
            except Exception as e:
                print(f"Failed to load provider module {module_name}: {e}")

def get_provider(provider_name: str) -> BaseProvider:
    """
    Get a provider instance by name.
    
    Args:
        provider_name: Name of the provider (e.g., 'openai', 'anthropic')
        
    Returns:
        Provider instance
        
    Raises:
        KeyError: If provider is not found
    """
    if provider_name not in PROVIDERS:
        raise KeyError(f"Provider '{provider_name}' not found. Available providers: {list(PROVIDERS.keys())}")
    
    return PROVIDERS[provider_name]

def list_providers() -> list[str]:
    """
    Get list of all available provider names.
    
    Returns:
        List of provider names
    """
    return list(PROVIDERS.keys())

def get_all_providers() -> Dict[str, BaseProvider]:
    """
    Get all registered providers.
    
    Returns:
        Dictionary mapping provider names to provider instances
    """
    return PROVIDERS.copy()

# Auto-discover providers when module is imported
_discover_providers()

# Make providers available at package level
__all__ = ['PROVIDERS', 'get_provider', 'list_providers', 'get_all_providers', 'BaseProvider']