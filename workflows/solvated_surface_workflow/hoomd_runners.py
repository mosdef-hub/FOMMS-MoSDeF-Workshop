"""Run HOOMD simulations for solvated surfaces."""
# Import Libraries
import os

import signac
import hoomd
import gsd
import unyt as u
import numpy as np
import fresnel
import IPython
import packaging
import math
import PIL
import io
import warnings
import mbuild as mb
import gmso

def example_run(job, parameterized_top, snapshot, forces, dt=0.00005):
    """Short 100 step run."""
    filter_ = hoomd.filter.Tags(list(np.arange(1900, parameterized_top.n_sites+1)))
    cpu = hoomd.device.CPU()
    sim = hoomd.Simulation(device=cpu, seed=int(job.sp.seed/1000))
    sim.create_state_from_snapshot(snapshot)
    temp = 30 * u.K # start at low temp
    kT = temp.to_equivalent("kJ/mol", "thermal").value
    sim.state.thermalize_particle_momenta(filter=filter_, kT=kT)
    integrator = hoomd.md.Integrator(
        dt=dt,
        forces=list(set().union(*forces.values())),
    )
    langevin = hoomd.md.methods.Langevin(
        filter=filter_,
        kT=kT,
        default_gamma=100
    )
    integrator.methods.append(langevin)
    sim.operations.integrator = integrator
    outlogger = hoomd.logging.Logger(categories=['scalar', 'string'])
    outlogger.add(sim, quantities=['timestep', 'tps'])
    thermodynamic_properties = hoomd.md.compute.ThermodynamicQuantities(
        filter=filter_
    )
    sim.operations.computes.append(thermodynamic_properties)
    outlogger.add(thermodynamic_properties, ['kinetic_temperature', "potential_energy"])
    table = hoomd.write.Table(
        trigger=hoomd.trigger.Periodic(period=10),
        logger=outlogger
    )
    sim.operations.writers.append(table)

    sim.run(100)
    hoomd.write.GSD.write(state=sim.state,
      mode='xb',
      filename=job.fn('100steps-out.gsd')
    )
    print("Finished 100 Steps of HOOMD-blue run")
    return sim

def nvt_run(job, parameterized_top, snapshot, forces):
    """Full NVT Simulation."""
    filter_ = hoomd.filter.Tags(list(np.arange(1900, parameterized_top.n_sites+1)))
    cpu = hoomd.device.CPU()
    sim = hoomd.Simulation(device=cpu, seed=job.sp.seed)
    sim.create_state_from_snapshot(snapshot)
    temp = 30 * u.K # start at low temp
    kT = temp.to_equivalent("kJ/mol", "thermal").value
    sim.state.thermalize_particle_momenta(filter=filter_, kT=kT)
    integrator = hoomd.md.Integrator(
        dt=0.00005,
        forces=list(set().union(*forces.values())),
    )
    langevin = hoomd.md.methods.Langevin(
        filter=filter_,
        kT=kT,
        default_gamma=100
    )
    integrator.methods.append(langevin)
    sim.operations.integrator = integrator
    outlogger = hoomd.logging.Logger(categories=['scalar', 'string'])
    outlogger.add(sim, quantities=['timestep', 'tps'])
    thermodynamic_properties = hoomd.md.compute.ThermodynamicQuantities(
        filter=filter_
    )
    sim.operations.computes.append(thermodynamic_properties)
    outlogger.add(thermodynamic_properties, ['kinetic_temperature', "potential_energy"])
    table = hoomd.write.Table(
        trigger=hoomd.trigger.Periodic(period=1000),
        logger=outlogger
    )
    sim.operations.writers.append(table)

    sim.run(50000)
    sim.operations.integrator.dt = 0.0005
    sim.run(25000)
    sim.operations.integrator.dt = 0.001
    sim.run(10000)

    #### MINIMIZATION DONE ########

    temp = job.sp.temperature * u.K
    kT = temp.to_equivalent("kJ/mol", "thermal").value
    sim.state.thermalize_particle_momenta(filter=filter_, kT=kT)
    langevin = hoomd.md.methods.Langevin(
        filter=filter_,
        kT=kT,
        default_gamma=1
    )
    sim.operations.integrator.methods = [langevin]
    sim.run(10000)


    ##### Equilibration at full temperature #######
    mttk = hoomd.md.methods.thermostats.MTTK(kT, tau=1)
    nvt = hoomd.md.methods.ConstantVolume(filter_, mttk)
    # add in thermo logger
    sim.operations.integrator.methods = [nvt]
    gsd_writer = hoomd.write.GSD(
        filename=job.fn('trajectory-nvt.gsd'),
        trigger=hoomd.trigger.Periodic(5000),
        mode='wb'
    )
    thermo_logger = hoomd.logging.Logger(categories=['scalar', 'string'])
    thermo_logger.add(sim, quantities=['timestep', 'tps'])
    thermo_logger.add(thermodynamic_properties, ['kinetic_temperature', "potential_energy"])
    gsd_writer.logger = thermo_logger
    sim.operations.writers.append(gsd_writer)
    sim.run(500000)
    hoomd.write.GSD.write(state=sim.state,
      mode='xb',
      filename=job.fn('production-out.gsd')
    )
    outlogger.flush()
    thermo_logger.flush()
    print("Finished 0.5 ns Steps of HOOMD-blue run")
    return sim

device = fresnel.Device()
tracer = fresnel.tracer.Path(device=device, w=300, h=300)
cer = fresnel.tracer.Path(device=device, w=300, h=300)

FRESNEL_MIN_VERSION = packaging.version.parse("0.13.0")
FRESNEL_MAX_VERSION = packaging.version.parse("0.14.0")


atom_colorDict = {
    "C": np.array([8, 143, 143]), "H":np.array([255, 255, 255]), "O":np.array([228, 70, 36]),
    "Si":np.array([231, 236, 65])
}
atom_sizeDict = {
    "C": 1, "H":0.5, "O":1,
    "Si":1
}

from collections.abc import Iterable
def render(snapshot, particles=None, is_solid=None, indices=None, indsDict=None):
    if indices is not None:
        assert issubclass(type(indices), Iterable)
    if ('version' not in dir(fresnel) or packaging.version.parse(
            fresnel.version.version) < FRESNEL_MIN_VERSION
            or packaging.version.parse(
                fresnel.version.version) >= FRESNEL_MAX_VERSION):
        warnings.warn(
            f"Unsupported fresnel version {fresnel.version.version} - expect errors."
        )
    N = snapshot.particles.N if indices is None else len(indices)
    L = snapshot.configuration.box[0]
    if particles is not None:
        N = len(particles)
    if is_solid is not None:
        N = len(indices)

    scene = fresnel.Scene(device)

    geometry = fresnel.geometry.Sphere(
        scene,
        N=N,
        #radius=.05
    )

    #geometry.material = fresnel.material.Material(
    #    color=fresnel.color.linear([0.01, 0.74, 0.26]),
    #    roughness=0.5
    #)
    geometry.material = fresnel.material.Material(
        roughness=0.5
    )
    geometry.material.primitive_color_mix = 1.0
    size_scalar=0.09
    for element, indsList in indsDict.items():
        geometry.color[indsList] = fresnel.color.linear(list(atom_colorDict[element] / 255))
        geometry.radius[indsList] = atom_sizeDict[element] * size_scalar
    if indices is None:
        geometry.position[:] = snapshot.particles.position[:]
    else:
        geometry.position[indices] = snapshot.particles.position[indices]


    geometry.outline_width = 0.0001
    box = fresnel.geometry.Box(scene,
                               snapshot.configuration.box,
                               box_radius=.02)

    scene.lights = [
        fresnel.light.Light(direction=(0, 0, 1),
                            color=(0.8, 0.8, 0.8),
                            theta=math.pi),
        fresnel.light.Light(direction=(1, 1, 1),
                            color=(1.1, 1.1, 1.1),
                            theta=math.pi / 3)
    ]
    scene.camera = fresnel.camera.Orthographic(position=(L * 2, L, L * 2),
                                               look_at=(0, 0, 0),
                                               up=(0, 0, 1),
                                               height=L * 1.4 + 1)
    scene.background_color = (1, 1, 1)
    return tracer.sample(scene, samples=10)


def render_movie(frames, job, particles=None, is_solid=None, indices=None):

    cpd = mb.load(job.fn("init.gro"))
    top = cpd.to_gmso()
    from gmso.core.element import element_by_symbol
    for site in top.sites:
        if site.name == "O_Sur":
            site.element_ = element_by_symbol("O")

    if is_solid is None:
        is_solid = [None] * len(frames)

    ## identify chemistry in topology
    indsDict = {"C":[], "H":[], "O":[], "Si":[]}
    for i,site in enumerate(top.sites):
        if indices is not None:
            if i not in indices:
                continue
        if site.element.symbol in atom_colorDict:
            indsDict[site.element.symbol].append(i)

    a = render(frames[0], indices=indices, indsDict=indsDict)

    im0 = PIL.Image.fromarray(a[:, :, 0:3], mode='RGB').convert(
        "P", palette=PIL.Image.Palette.ADAPTIVE
    )
    ## identify ehcemical compounds
    ims = []
    for i, f in enumerate(frames[1::2]):
        a = render(f, indices=indices, indsDict=indsDict)
        im = PIL.Image.fromarray(a[:, :, 0:3], mode='RGB')
        im_p = im.quantize(palette=im0)
        ims.append(im_p)

    blank = np.ones(shape=(im0.height, im0.width, 3), dtype=np.uint8) * 255
    im = PIL.Image.fromarray(blank, mode='RGB')
    im_p = im.quantize(palette=im0)
    ims.append(im_p)

    f = io.BytesIO()
    im0.save(f, 'gif', save_all=True, append_images=ims, duration=1000, loop=0)

    size = len(f.getbuffer()) / 1024
    if (size > 1000):
        warnings.warn(f"Large GIF: {size} KiB")
    return IPython.display.display(IPython.display.Image(data=f.getvalue()))
