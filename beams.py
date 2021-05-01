import math
from functools import cached_property

# Cost of electricity in [$/J] (converted from [$/kWh])
ELECTRICITY_COST = 0.314 / 10**3 / 3600

class Material:
    """
    Class to store the various properties of a material. Could be a dict,
    but where's the fun in that?
    """
    electricity_cost = ELECTRICITY_COST

    def __init__(self, name, yield_stress, modulus, elongation, density, price, energy_density):
        self.name = name
        self.yield_stress = yield_stress
        self.modulus = modulus
        self.elongation = elongation
        self.density = density
        self.price = price
        self.energy_density = energy_density


class Beam:
    """
    Base class for Beam objects since a lot of the calculations for properties
    of the beam are essentially the same. To work well, we obviously need to 
    make sure all the expected properties are well-defined in the subclass.

    Keep everything in vanilla SI units (no prefixes like Mega, etc.) to avoid
    any confusion with unit conversion!

    In order to make the best use of this, subclass it for your chosen 
    cross-sectional shape, and add properties to determine:
        * `area`
        * `second_moment_of_area_xx`
        * `second_moment_of_area_yy`

    Some other attributes should be included in the initialiser of your subclass:
        * `length`
        * 
    """

    def __init__(self, material: Material):
        self.material = material

    @cached_property
    def volume(self):
        """
        Returns volume of beam [m^3] if `area` and `length` are defined.
        """
        try:
            return self.area * self.length
        except (AttributeError, TypeError):
            return None

    @cached_property
    def mass(self):
        """
        Returns mass of beam [kg] if `volume` is defined.
        """
        try:
            return self.volume * self.material.density
        except (AttributeError, TypeError):
            return None

    @cached_property
    def cost(self):
        """
        Returns cost of beam [$] if `mass` is defined.
        """
        try:
            return self.mass * self.material.price
        except (AttributeError, TypeError):
            return None

    @cached_property
    def total_embodied_energy(self):
        """
        Returns embodied energy of beam [J] if `mass` is defined.
        """
        try:
            return self.mass * self.material.energy_density
        except (AttributeError, TypeError):
            return None
    
    @cached_property
    def embodied_energy_cost(self):
        try:
            return self.total_embodied_energy * self.material.electricity_cost
        except (AttributeError, TypeError):
            return None

    @cached_property
    def total_cost(self):
        try:
            return self.cost + self.embodied_energy_cost
        except (AttributeError, TypeError):
            return None

    @cached_property
    def buckling_load(self):
        """
        Returns buckling load (minimum of XX and YY axes) of beam [N] if 
        `second_moment_of_area_xx`, `second_moment_of_area_yy`, and `length` 
        are defined.

        NOTE: Assumes pin-pin connection so effective length factor is exactly
        1!
        """
        try:
            min_I = min(self.second_moment_of_area_xx,
                        self.second_moment_of_area_yy)

            # Assume pin-pin connection (i.e. effective length = 1 * length)
            min_buckling_load = math.pi**2 * self.material.modulus * min_I / self.length ** 2
            return min_buckling_load
        except (AttributeError, TypeError):
            return None

    @cached_property
    def squash_load(self):
        """
        Returns squash/yielding load of beam [N] if `area` is defined.
        """
        try:
            return self.material.yield_stress * self.area
        except (AttributeError, TypeError):
            return None

    def get_strain(self, loading):
        """
        Returns strain on beam if `area` is defined.
        """
        try:
            stress = loading / self.area
            strain = stress / self.material.modulus
            return strain
        except (AttributeError, TypeError):
            return None

    def is_sufficient(self, loading):
        """
        Compares this beam's `squash_load` and `buckling_load` against the 
        given `loading` to determine whether it would fail or not. ALSO checks
        if the strain under the loading is less than the material's elongation,
        to ensure only plastic deformation!

        Returns `True` if the beam would NOT fail (i.e. IS sufficient), `False` 
        otherwise.
        """
        try:
            strain = self.get_strain(loading)
            return self.squash_load >= loading and self.buckling_load >= loading and strain <= self.material.elongation
        except (AttributeError, TypeError):
            return None

    def get_new_best_beam(self, loading, curr_best_beam):
        """
        Compares this beam with the current best beam. Returns this beam if
        it is actually better, otherwise just returns given `curr_best_beam`.

        This is intended to be used in a (nested) for loop going over all
        possible combinations of dimensions for this beam, in order to determine
        the minimal area (and subsequent maximal second moments of area if 
        possible) required for this beam design.
        """
        if self.is_sufficient(loading):
            # Make sure we have a best beam to "compare" with at start
            if curr_best_beam is None:
                curr_best_beam = self

            if self.area < curr_best_beam.area:
                best_beam = self
            elif self.area == curr_best_beam.area:
                # Compare moments of inertia. If this beam is
                # bigger in every way for same area, might as well
                # use it!
                Ix = self.second_moment_of_area_xx
                best_Ix = curr_best_beam.second_moment_of_area_xx
                Iy = self.second_moment_of_area_yy
                best_Iy = curr_best_beam.second_moment_of_area_yy

                # Can we get a stronger beam for the same area? Yes, sometimes!
                if Ix > best_Ix and Iy > best_Iy:
                    curr_best_beam = self

        return curr_best_beam


class RHSBeam(Beam):
    """
    A Rectangular Hollow Section (RHS) beam.
    """

    def __init__(self, material: Material, length, b, h, t):
        """
        Parameters
        ----------
        material: Material
            Material chosen for this beam.
        length: int or float
            The length [m] of this beam.
        b: int or float
            The breadth [m] of this beam's cross-section.
        h: int or float
            The height [m] of this beam's cross-section.
        t: int or float
            The thickness [m] of the walls of this beam.
        """
        super().__init__(material)

        self.length = length
        self.b = b
        self.h = h
        self.t = t

    @cached_property
    def area(self):
        return self.b*self.h - (self.b - 2*self.t) * (self.h - 2*self.t)

    @cached_property
    def second_moment_of_area_xx(self):
        b, h, t = self.b, self.h, self.t

        I_big = b * h**3 / 12
        I_small = (b - 2*t)*(h - 2*t)**3 / 12
        return I_big - I_small

    @cached_property
    def second_moment_of_area_yy(self):
        b, h, t = self.b, self.h, self.t

        I_big = h * b**3 / 12
        I_small = (h - 2*t)*(b - 2*t)**3 / 12
        return I_big - I_small


class CHSBeam(Beam):
    def __init__(self, material: Material, length, r, t):
        """
        Parameters
        ----------
        material: Material
            Material chosen for this beam.
        length: int or float
            The length [m] of this beam.
        r: int or float
            The total radius [m] of this beam's cross-section (i.e., including
            the thickness of the walls).
        t: int or float
            The thickness [m] of the walls of this beam.
        """
        super().__init__(material)

        self.length = length
        self.r = r
        self.t = t

    @cached_property
    def area(self):
        r, t = self.r, self.t
        # Simplified calcuation for area of CHS
        return math.pi * (2 * r * t - t**2)

    @cached_property
    def second_moment_of_area_xx(self):
        return math.pi / 4 * (self.r**4 - (self.r - self.t)**4)

    @cached_property
    def second_moment_of_area_yy(self):
        # By symmetry
        return self.second_moment_of_area_xx


class IBeam(Beam):
    """
    An I-beam (sometimes known as H-beam too).
    """

    def __init__(self, material: Material, length, b, h, tw, tf):
        """
        Parameters
        ----------
        material: Material
            Material chosen for this beam.
        length: int or float
            The length [m] of this beam.
        b: int or float
            The breadth [m] of this beam's cross-section (i.e. width of 
            flanges).
        h: int or float
            The total height [m] of this beam's cross-section (i.e., including
            height of flanges).
        tw: int or float
            The thickness [m] of the webbing of this beam.
        tf: int or float
            The thickness [m] of the flanges of this beam.
        """
        super().__init__(material)

        self.length = length
        self.b = b
        self.h = h
        self.tw = tw
        self.tf = tf

    @cached_property
    def area(self):
        a_flanges = 2 * self.b * self.tf
        a_web = self.tw * (self.h - 2 * self.tf)
        return a_flanges + a_web

    @cached_property
    def second_moment_of_area_xx(self):
        # We represent the I-beam as a large rectangle minus two rectangles
        # either side.
        I_big = self.b * self.h**3 / 12
        b_small = (self.b - self.tw) / 2
        h_small = self.h - 2 * self.tf
        I_small = b_small * h_small**3 / 12
        I = I_big - 2 * I_small
        return I

    @cached_property
    def second_moment_of_area_yy(self):
        # Break beam up into its two flanges plus its web
        I_flange = self.tf * self.b**3 / 12
        I_web = (self.h - 2*self.tf) * self.tw**3 / 12
        I = 2 * I_flange + I_web
        return I
