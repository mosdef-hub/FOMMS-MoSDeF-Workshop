# FOMMS-MoSDeF-Workshop

Welcome to the MoSDeF tutorial at FOMMS 2024 

## About MoSDeF
The Molecular Simulation Design Framework, or MoSDeF, is an collaborative project focus on developing an open-source software suite to assist with the preparation of chemical/biological systems for molecular simulation. The framework strives to create tools that are
- Non-specific
- Force field agnostic
- Engine agnostic

These principals allow for the creation of more diverse workflow, that is, utilizing multiple simulation engines to perform each steps of the simulation process, and simulate systems at multiple scales, e.g, ab initio, atomistic, coarse-grained, and more. Most importantly, the MoSDeF software suite trivialize the distribution of the system's initialization, and parameterization process, ensure their reproducibility by the general community.

The MoSDeF software suite consist of three core libraries, namely [mBuild](https://github.com/mosdef-hub/mbuild), [Foyer](https://github.com/mosdef-hub/foyer), and [GMSO](https://github.com/mosdef-hub/gmso). Each library dedicates to handle a certain step of the chemical system initialization process, as summarized in the figure below.

<p align="center">
    <img src="images/mosdef_scheme.jpg" width="500"/>
</p>

## The MoSDeF Workflow: Towards TRUE Simulations
Transparent, Reproducible, Usable by others, and Extensible (TRUE) are four criteria for published computational simulation research introduced by Thompson et al. The TRUE criteria are introduced to encounter the (ir)reproducibility issues in the community, which, in many cases, can be attributed to:
- Human error
- Incomplete reports of simulation workflow
- Unpublished codes

The MoSDeF provides necessary tools to automate the simulation workflow in a scriptable manners, eliminating unnecessary manual interaction with the established workflow, and simplify the distribution of codes utilized for the system initialization process, and assist with the adherence to the TRUE criteria.

## MoSDeF Tutorial

In this tutorial, we will walk through a series of simulation workflows, all using MoSDeF to create the chemical/biological systems, parameterize, and write out to different file formats that can be taken in by various simulation engines.
Through these workflow, we want to demonstrate how our libraries can be used to design TRUE (Transferable, Reproducible, Usable-by-other, and Extensible) studies, and ensure FAIR (Findable, Accesible, Interoperable, and Reusable) data management.

### Installation Instruction

These tutotial workflows are designed to work on Google Colab. User can access these notebooks through the below links:

LINKS

### Other useful resources

More in-depth MoSDeF tutorials: https://github.com/mosdef-hub/mosdef_tutorials

Example MoSDeF workflow: https://github.com/mosdef-hub/mosdef-workflows

Documentations:

    - https://mbuild.mosdef.org/en/stable/
    - https://foyer.mosdef.org/en/stable/
    - https://gmso.mosdef.org/en/stable/


<p align="center">
    <img src="images/mosdef_logo.svg"/>
</p>
