#!/usr/bin/env python3
"""RemoteLAN – la stessa app su tutti i PC (vedi README.md).

    python remotelan_app.py              rende controllabile questo PC + finestra "Connetti"
    python remotelan_app.py --agent      solo agente in background (PC da controllare)
    python remotelan_app.py --viewer     solo finestra "Connetti"
"""
from remotelan.app import main

if __name__ == "__main__":
    main()
