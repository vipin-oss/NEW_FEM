# The extensional coupling factor of the plate, from the material
constants and from the finite element model

## Step 1 -- the record (poling along $x$, so the polar axis is `3`)

```
C11=2.220e+11  C12=1.080e+11  C13=1.110e+11  C33=1.510e+11  C44=6.100e+10  Pa
e31=-0.7  e33=+6.7  e15=+34.2  C/m^2
kappa_r11=2200  kappa_r33=56 (kappa33 = 4.9583e-10 F/m)
```

3-D stiffness in the $(x,y,z)$ frame, polar axis first:

```
   15.1000   11.1000   11.1000
   11.1000   22.2000   10.8000
   11.1000   10.8000   22.2000
```  (units $10^{10}$ Pa)

## Step 2 -- 3-D free bar (all normal strains free)

$$x_{3D}=\frac{\mathbf e_3^{\mathsf T}\mathbf s_3\mathbf e_3}{\kappa_{33}},\qquad \mathbf e_3=(e_{33},e_{31},e_{31}),\qquad k^2=\frac{x_{3D}}{1+x_{3D}}$$

```
   13.1015  -4.4069  -4.4069
  -4.4069   7.3834  -1.3885
  -4.4069  -1.3885   7.3834
```  (compliance, units $10^{-12}$ Pa$^{-1}$)

e3' s3 e3 = 6.766730e-10 m^4/N,   kappa33 = 4.958345e-10 F/m
x_3D = 1.364715   ->   k^2_3D,free = **0.57712**

For comparison the blocked (1-D) textbook value $k_{33}^2=e_{33}^2/(C_{33}\kappa_{33})$ is 0.59956, whose free form $x/(1+x)$ is 0.37483 -- that is the 'uniaxial' column below.

## Step 3 -- plane-stress reduction, $\sigma_{zz}=0$

The out-of-plane normal stress is condensed exactly as the material adapter does it:

$$\mathbf C_p=\mathbf C_{2d}-\mathbf c_3\mathbf c_3^{\mathsf T}/C_{33}^{(zz)},\qquad \mathbf c_3=(C_{xz},C_{yz})$$

```
C_2d =
   15.1000   11.1000
   11.1000   22.2000   (1e10 Pa)
c3   = (11.1000, 10.8000)   (1e10 Pa)
C_zz = 22.2000   (1e10 Pa)
C_p  =
   9.5500   5.7000
   5.7000   16.9459   (1e10 Pa)
```

i.e. $C^p_{11}=9.5500e+10$, $C^p_{12}=5.7000e+10$, $C^p_{22}=1.6946e+11$ Pa, $C_{44}=6.1000e+10$ Pa for $\gamma_{xy}$.

Consistency check built into the reduction: the plane-stress compliance must be the corresponding block of the 3-D compliance, $\mathbf C_p^{-1}=(\mathbf s_3)_{2\times2}$; here the difference is 3.2e-27 Pa$^{-1}$.

The piezoelectric matrix is *not* reduced: with $\sigma_{zz}=0$ and $D_z=0$ the out-of-plane normal strain couples only to $e_{31}$ terms that the in-plane block already carries, so $\mathbf e_p=\mathbf e_{2d}$ and $\kappa_{\rm eff}=\kappa_{xx}=\kappa_{33}$.

## Step 4 -- the 2-D closed form

$$x_{2D}=\frac{\mathbf e_p^{\mathsf T}\mathbf C_p^{-1}\mathbf e_p}{\kappa_{xx}},\qquad k^2=\frac{x_{2D}}{1+x_{2D}}$$

```
e_p   = (+6.7000, -0.7000, +0.0000)   C/m^2
C_p^-1 =
   1.3101  -0.4407
  -0.4407   0.7383   (1e-11 /Pa)
e'C^-1 e = 6.330795e-10 C^2/(N m^2)
kappa_xx = 4.958345e-10 F/m
x_2D   = 1.276796
k^2    = 1.276796/(1+1.276796) = **0.56079**
```

By hand, for a reader who wants to check the arithmetic: $\det C_p=1.293438e+22$, $\mathbf e_p^{\mathsf T}\mathbf C_p^{-1}\mathbf e_p=6.3308e-10$, so $x=1.2768$ and $k^2=0.56079$.

## Step 5 -- closed form against the finite element model

| value | $x$ | $k^2$ |
|---|---|---|
| closed form | 1.27680 | **0.56079** |
| FEM free 48x4 | 1.27680 | **0.56079** |
| FEM clamped 48x4 | 1.27052 | **0.55957** |
| FEM clamped 24x2 | 1.26676 | **0.55884** |
| FEM clamped 96x4 | 1.27229 | **0.55992** |
| closed form, plane strain | 1.05409 | **0.51317** |
| FEM clamped 48x4, plane strain | 1.04705 | **0.51149** |

3-D free bar for reference: $x=1.36472$, $k^2=0.57712$ (not attainable in a plane-stress model).

- closed form $-$ FEM free plate (48x4): -0.0000 %
- closed form $-$ FEM clamped (48x4): -0.2167 %
- mesh: 24x2 vs 48x4 clamped: -0.1303 %, 96x4 vs 48x4: +0.0616 %

## Step 6 -- why the earlier number was 0.3582

The helper that produced it (`_static_k2`) solved the coupling against the *open-circuit* matrix $K_{oc}$ and then applied the same $x/(1+x)$ map.  But

$$K_{oc}=K_{sc}+\frac{d d^{\mathsf T}}{\beta}\;\Longrightarrow\;\frac{d^{\mathsf T}K_{oc}^{-1}d}{\beta}=x-\frac{x^2}{1+x}=\frac{x}{1+x}=k^2$$

by Sherman--Morrison, so the first application already returned $k^2$ and the second turned it into $k^2/(1+k^2)$:

| $h$ (µm) | correct $k^2$ | $k^2/(1+k^2)$ | recorded as |
|---|---|---|---|
| 10 | 0.55814 | 0.35821 | 0.35821 |
| 5 | 0.55843 | 0.35833 | 0.35833 |
| 2 | 0.55858 | 0.35839 | 0.35839 |
| 1 | 0.55861 | 0.35840 | 0.35840 |

The identity reproduces all four recorded values to the last digit, which is the proof that the 0.3582 series was the same physics run through the same formula twice -- not a different material, geometry or mesh.

