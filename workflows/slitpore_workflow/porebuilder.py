'''
This code is based on the code written by Ray Matsumoto  at https://github.com/PTC-CMC/Pore-Builder.
The name of the functions have remained the same.
'''

import mbuild as mb
import numpy as np

__all__ = ['GraphenePore']


class GraphenePore(mb.Compound):
    """A general slit pore recipe.

    Parameters
    ----------
    pore_length : int, default=4
        dimensions of graphene sheet length in nm
    pore_depth : int, default=4
        dimensions of graphene sheet depth in nm
    n_sheets : int, default=3
        number of parallel graphene sheets
    pore_width: int, default=1
        width of slit pore in nm
    slit_pore_dim : int, default=1
        dimension slit pore, default is in the y-axis
    box: str, default= lattice


    Attributes
    ----------
    see mbuild.Compound

    """
    def __init__(self, pore_length=4, pore_depth=3, n_sheets=3, pore_width=1, slit_pore_dim=1, box = "lattice"):
        super(GraphenePore, self).__init__()

        factor = np.cos(np.pi/6)
        # Estimate the number of lattice repeat units
        replicate = [int(pore_length/0.2456), (pore_depth/0.2456)*(1/factor)]
        if all(x <= 0 for x in [pore_length, pore_depth]):
            msg = 'Dimension of graphene sheet must be greater than zero'
            raise ValueError(msg)
        carbon = mb.Compound(name="C", element="C")
        carbon_locations = [[0, 0, 0], [2/3, 1/3, 0]]
        basis = {carbon.name: carbon_locations}
        lattice_spacing = [0.2456, 0.2456, 0.335]
        angles = [90.0, 90.0, 120.0]

        graphene_lattice = mb.Lattice(lattice_spacing=lattice_spacing,
                                      angles=angles, lattice_points=basis)

        graphene = graphene_lattice.populate(compound_dict={carbon.name: carbon},
                                             x=replicate[0], y=replicate[1],
                                             z=n_sheets)

        for particle in graphene.particles():
            if particle.xyz[0][0] < 0:
                particle.xyz[0][0] += graphene.box.Lx

        bot_sheet = mb.clone(graphene)
        bot_sheet.name = 'BOT'
        top_sheet = mb.clone(graphene)
        if slit_pore_dim == 0:
            bot_sheet.spin(1.5708, [0, 1, 0])
            top_sheet.spin(1.5708, [0, 1, 0])
            top_sheet.translate([pore_width + (graphene.periodicity[2] - 0.335), 0, 0])
        elif slit_pore_dim == 1:
            bot_sheet.spin(1.5708, [1, 0, 0])
            top_sheet.spin(1.5708, [1, 0, 0])
            top_sheet.translate([0, pore_width + (graphene.periodicity[2] - 0.335), 0])
        elif slit_pore_dim == 2:
            top_sheet.translate([0, 0, pore_width + (graphene.periodicity[2] - 0.335)])
        top_sheet.name = 'TOP'
        self.add(top_sheet)
        self.add(bot_sheet)
        self.xyz -= np.min(self.xyz, axis=0)
        if box == "tight":
            self.box = self.get_boundingbox(pad_box = 0.08)
        elif box == "lattice":
            self.box = self.get_boundingbox(pad_box = lattice_spacing[2])
