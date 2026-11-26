#!/usr/bin/env python3
"""LBS Labs Remote – la stessa app su tutti i PC (vedi README.md).

    python lbs_labs_remote.py              rende controllabile questo PC + finestra "Connetti"
    python lbs_labs_remote.py --agent      solo agente in background (PC da controllare)
    python lbs_labs_remote.py --viewer     solo finestra "Connetti"
"""
from lbsremote.app import main

if __name__ == "__main__":
    main()
