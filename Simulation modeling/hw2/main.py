### modified Bass model code ###

from pathlib import Path

from pysd.py_backend.statefuls import Integ
from pysd import Component

__pysd_version__ = "3.13.4"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 10,
    "time_step": lambda: 0.01,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    The final time for the simulation.
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    The initial time for the simulation.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    The frequency with which output is stored.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def time_step():
    """
    The time step for the simulation.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="potential customer concentration",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potential_customers": 1, "total_market": 1},
)
def potential_customer_concentration():
    return potential_customers() / total_market()


@component.add(
    name="new customers",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"word_of_mouth_demand": 1},
)
def new_customers():
    return word_of_mouth_demand()


@component.add(
    name="contacts of noncustomers with customers",
    units="contact/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"contacts_with_customers": 1, "potential_customer_concentration": 1},
)
def contacts_of_noncustomers_with_customers():
    return contacts_with_customers() * potential_customer_concentration()


@component.add(
    name="contacts with customers",
    units="contact/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"customers": 1, "sociability": 1},
)
def contacts_with_customers():
    return customers() * sociability()


@component.add(
    name="Customers",
    units="person",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_customers": 1},
    other_deps={"_integ_customers": {"initial": {}, "step": {"new_customers": 1}}},
)
def customers():
    return _integ_customers()


_integ_customers = Integ(lambda: new_customers(), lambda: 1000, "_integ_customers")


@component.add(
    name="fruitfulness",
    units="person/contact",
    comp_type="Constant",
    comp_subtype="Normal",
)
def fruitfulness():
    return 0.01


@component.add(
    name="Potential Customers",
    units="person",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_potential_customers": 1},
    other_deps={
        "_integ_potential_customers": {"initial": {}, "step": {"new_customers": 1}}
    },
)
def potential_customers():
    return _integ_potential_customers()


_integ_potential_customers = Integ(
    lambda: -new_customers(), lambda: 1000000.0, "_integ_potential_customers"
)


@component.add(
    name="sociability",
    units="contact/person/Month",
    comp_type="Constant",
    comp_subtype="Normal",
)
def sociability():
    return 20


@component.add(
    name="total market",
    units="person",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"customers": 1, "potential_customers": 1},
)
def total_market():
    return customers() + potential_customers()


@component.add(
    name="word of mouth demand",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"contacts_of_noncustomers_with_customers": 1, "fruitfulness": 1},
)
def word_of_mouth_demand():
    return contacts_of_noncustomers_with_customers() * fruitfulness()
