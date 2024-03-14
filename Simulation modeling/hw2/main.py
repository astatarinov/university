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
    "final_time": lambda: 200,
    "time_step": lambda: 0.1,
    "saveper": lambda: 10*time_step(),
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

### basic constants ###

@component.add(
    name="marketing efficiency",
    units="person/contact",
    comp_type="Constant",
    comp_subtype="Normal",
)
def marketing_efficiency():
    return 0.011

@component.add(
    name="fruitfulness",
    units="person/contact",
    comp_type="Constant",
    comp_subtype="Normal",
)
def fruitfulness():
    return 0.015

@component.add(
    name="sociability",
    units="contact/person/Month",
    comp_type="Constant",
    comp_subtype="Normal",
)
def sociability():
    return 50

### customer type proportions ###

@component.add(
    name="p11",
    units="satisfied customers/all customers",
    comp_type="Constant",
    comp_subtype="Normal",
)
def p11():
    return 0.2

@component.add(
    name="p13",
    units="unsatisfied customers/all customers",
    comp_type="Constant",
    comp_subtype="Normal",
)
def p13():
    return 0.2

@component.add(
    name="p21",
    units="satisfied competitor customers/all competitor customers",
    comp_type="Constant",
    comp_subtype="Normal",
)
def p21():
    return 0.2

@component.add(
    name="p23",
    units="unsatisfied competitor customers/all competitor customers",
    comp_type="Constant",
    comp_subtype="Normal",
)
def p23():
    return 0.2

### leaving to pc rate
@component.add(
    name="leave_rate",
    units="probabilty",
    comp_type="Constant",
    comp_subtype="Normal",
)

def leave_rate():
    return marketing_efficiency() / (marketing_efficiency() + fruitfulness())

### leaving to competitor rate
@component.add(
    name="change_rate",
    units="probabilty",
    comp_type="Constant",
    comp_subtype="Normal",
)

def change_rate():
    return fruitfulness() / (marketing_efficiency() + fruitfulness())

### Customers

@component.add(
    name="potential customer concentration",
    units="dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potential_customers": 1, "total_market": 1},
)
def potential_customer_concentration():
    return potential_customers() / total_market()

# PC -> 'us'
@component.add(
    name="new customers",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"word_of_mouth_demand": 1, "direct_marketing": 1},
)
def new_customers():
    return word_of_mouth_demand() + direct_marketing()


#  PC -> comp
@component.add(
    name="competitor new customers",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"word_of_competitive_mouth_demand": 1, "direct_marketing": 1},
)
def competitor_new_customers():
    return word_of_competitive_mouth_demand() + direct_marketing()


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
    other_deps={
        "_integ_customers": {
            "initial": {},
            "step": {"new_customers": 1, "churn": 1, "changed": 1, "competitor_changed": 1}
        }
    },
)
def customers():
    return _integ_customers()


_integ_customers = Integ(
        lambda: new_customers() - churn() - changed() + competitor_changed(),
        lambda: 1000, "_integ_customers"
    )

@component.add(
    name="Competitor customers",
    units="person",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_competitor_customers": 1},
    other_deps={
        "_integ_competitor_customers": {
            "initial": {},
            "step": {"competitor_new_customers": 1, "churn_competitor": 1,
                     "competitor_changed": 1, "changed": 1}
        }
    },
)
def competitor_customers():
    return _integ_competitor_customers()


_integ_competitor_customers = Integ(
    lambda: competitor_new_customers() - churn_competitor() - competitor_changed() + changed(),
    lambda: 1000, "_integ_competitor_customers"
)

# Our market share 
@component.add(
    name="market share",
    units="percentage",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"customers": 1, "total_market": 1},
)
def market_share():
    return customers() / total_market()

# Competitor market share
@component.add(
    name="competitor share",
    units="percentage",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"competitor_customers": 1, "total_market": 1},
)
def competitor_share():
    return competitor_customers() / total_market()


# Proportion 
@component.add(
    name="proportion",
    units="percentage",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"customers": 1, "competitor_customers": 1},
)
def proportion():
    return customers() / competitor_customers()


# our customers -> PC
@component.add(
    name="churn",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"leave_rate": 1, "p13": 1, "customers": 1},
)
def churn():
    return leave_rate() * p13() * customers()

# comp -> PC
@component.add(
    name="competitor left",
    units="person/month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"competitor_customers": 1, "p23": 1, "leave_rate": 1},
)
def churn_competitor():
    return competitor_customers() * p23() * leave_rate()

# our customers -> competitor 
@component.add(
    name="changed",
    units="person/month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"competitor_customers": 1,
                "p13": 1, "p11": 1, "p21": 1, "leave_rate": 1,
                "change_rate": 1, "fruitfulness": 1, "sociability": 1},
)
def changed():
    return (
        fruitfulness() * sociability() * customers() * p21() * competitor_share() 
        * (1 - p13() * change_rate() - p11()) * leave_rate()
    )

# competitor customers -> us 

@component.add(
    name="competitor changed",
    units="person/month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"competitor_customers": 1, "leave_rate": 1,
                "p23": 1, "p11": 1, "p21": 1, "market_share": 1,
                "change_rate": 1, "fruitfulness": 1, "sociability": 1},
)
def competitor_changed():
    return (
        fruitfulness() * sociability() * competitor_customers() * p11() * market_share()
        * (1 - p23() * change_rate() - p21()) * leave_rate()
    )


@component.add(
    name="Potential Customers",
    units="person",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_potential_customers": 1},
    other_deps={
        "_integ_potential_customers": {
            "initial": {},
            "step": {"new_customers": 1, "competitor_new_customers": 1,
                     "churn_competitor": 1, "churn": 1}
        }
    },
)
def potential_customers():
    return _integ_potential_customers()


_integ_potential_customers = Integ(
    lambda: -new_customers() - competitor_new_customers() + churn_competitor() + churn(),
    lambda: 100_000.0, "_integ_potential_customers"
)

@component.add(
    name="total market",
    units="person",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"customers": 1, "potential_customers": 1, "competitor_customers": 1},
)
def total_market():
    return customers() + potential_customers() + competitor_customers()


@component.add(
    name="word of mouth demand",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"contacts_of_noncustomers_with_customers": 1, "fruitfulness": 1},
)
def word_of_mouth_demand():
    return fruitfulness()*sociability()*potential_customers()*customers()*p11()/total_market()


@component.add(
    name="contacts with competitor customers",
    units="contact/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"competitor_customers": 1, "sociability": 1, "p11": 1},
)
def contacts_with_competitor_customers():
    return competitor_customers() * sociability() * p11()


@component.add(
    name="contacts of noncustomers with competitive customers",
    units="contact/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"contacts_with_competitor_customers": 1,
                "potential_customer_concentration": 1, "p21": 1},
)
def contacts_of_noncustomers_with_competitive_customers():
    return contacts_with_competitor_customers() * potential_customer_concentration() * p21()


@component.add(
    name="word of competitive mouth demand",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"contacts_of_noncustomers_with_competitive_customers": 1, "fruitfulness": 1},
)
def word_of_competitive_mouth_demand():
    return fruitfulness()*sociability()*potential_customers()*competitor_customers()*p21()/total_market()

# contacts_of_noncustomers_with_competitive_customers() * fruitfulness()


@component.add(
    name="direct marketing",
    units="person/Month",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"potential_customers": 1, "marketing_efficiency": 1},
)
def direct_marketing():
    return potential_customers() * marketing_efficiency()
