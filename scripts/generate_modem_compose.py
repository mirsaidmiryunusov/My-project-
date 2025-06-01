#!/usr/bin/env python3
"""
Modem Compose Generator Script

This script generates a comprehensive Docker Compose configuration for
80 SIM900 modem-daemon instances, providing automated deployment and
management of the complete modem infrastructure for Project GeminiVoiceConnect.
"""

import os
import yaml
from typing import Dict, Any, List


def generate_modem_compose() -> Dict[str, Any]:
    """Generate Docker Compose configuration for 80 modem daemons."""
    
    compose_config = {
        'version': '3.8',
        'services': {},
        'volumes': {},
        'networks': {
            'gemini-network': {
                'external': True
            }
        }
    }
    
    # Generate 80 modem daemon services
    for modem_id in range(1, 81):
        modem_id_str = f"{modem_id:03d}"
        usb_device = f"/dev/ttyUSB{modem_id - 1}"
        
        service_name = f"modem-daemon-{modem_id_str}"
        volume_name = f"modem_data_{modem_id_str}"
        
        # Service configuration
        service_config = {
            'build': {
                'context': './modem-daemon',
                'dockerfile': 'Dockerfile'
            },
            'container_name': f"gemini-{service_name}",
            'environment': [
                f"MODEM_ID={modem_id_str}",
                f"MODEM_DEVICE={usb_device}",
                "REDIS_URL=redis://redis:6379/3",
                "CORE_API_URL=http://core-api:8001",
                "VOICE_BRIDGE_URL=http://voice-bridge:8000"
            ],
            'devices': [
                f"{usb_device}:{usb_device}"
            ],
            'volumes': [
                f"{volume_name}:/app/data"
            ],
            'depends_on': [
                'redis',
                'core-api',
                'voice-bridge'
            ],
            'networks': [
                'gemini-network'
            ],
            'restart': 'unless-stopped'
        }
        
        compose_config['services'][service_name] = service_config
        compose_config['volumes'][volume_name] = {}
    
    return compose_config


def main():
    """Main function to generate modem configurations."""
    config = generate_modem_compose()
    
    with open('docker-compose.modems.yml', 'w') as f:
        f.write("# Generated Docker Compose for 80 SIM900 modem daemons\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print("✓ Generated docker-compose.modems.yml with 80 modem instances")


if __name__ == "__main__":
    main()