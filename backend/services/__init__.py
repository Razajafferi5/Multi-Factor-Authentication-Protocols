"""Business-logic services shared by the REST API and the dashboard.

These modules are deliberately framework-agnostic: they accept a SQLAlchemy
session plus plain data and return plain data, so they can be driven by Flask
routes (HTTP mode) or imported directly by the Streamlit dashboard (EMBEDDED
mode).
"""
