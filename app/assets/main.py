import asyncio
import os
import pandas as pd
import getpass
from tqdm import tqdm
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError




def mostrar_menu():
    print("\n" + "="*40)
    print(" BOT WIZARD (Especiales)")
    print("="*40)
    print("1. Iniciar Sesion")
    print("2. Cierre Folio Wizard")
    print("3. Adjuntar Informe SUGO")
    print("4. Salir")
    print("="*40)

# --- MENÚ PRINCIPAL ---
if __name__ == "__main__":

    while True:
        mostrar_menu()
        op = input("Seleccione: ")
        if op == '1':
            asyncio.run(autenticar_google())
        elif op == '2':
            asyncio.run(orchestrator("wizard", modo_oculto=False))
        elif op == '3':
            asyncio.run(orchestrator("sugo", modo_oculto=False))
        elif op == '4':
            break