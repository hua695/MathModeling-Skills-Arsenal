from setuptools import setup


setup(
    name="tech-route-maker",
    version="0.3.0",
    description="Evidence-grounded editable technical route diagrams for research and engineering projects.",
    packages=["tech_route_maker", "scripts"],
    entry_points={"console_scripts": ["trm=tech_route_maker.cli:main"]},
)
