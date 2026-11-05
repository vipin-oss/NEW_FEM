%% FEM6_memory_piezo_SG_2D_v2.m
% FEM-6: fractional-memory (Caputo) piezoelectric strain-gradient model on
% the FEM-1 BFS C1 element.  Corrected version of FEM6_memory_piezo_SG_2D.m.
%
% Fixes relative to v1 (details in docs/FEM6_checker_report.md):
%
%  1. NONLOCAL TENSOR.  The strain-gradient stiffness is assembled as
%         Kg = 1/2 * int  M_mn (B_,m' C B_,n)  dA ,
%     with M the second-moment tensor of the averaging domain:
%         cuboid    (half-widths a_x,a_y):  M = diag(a_x^2/3, a_y^2/3)
%         ellipsoid (semi-axes  l_x,l_y):   M = diag(l_x^2/5, l_y^2/5)
%     The 1/2 is universal.  v1 used 1/10 * diag(l^2), i.e. 1/2 * (l^2/5):
%     correct for an ellipsoid, but pairing a cuboid M with the coefficient
%     1/10 overestimates Kg by a factor of 5.
%
%  2. L1 WEIGHTS.  The Caputo derivative at t_n needs b_0..b_{n-1} with
%     b_k = (k+1)^(1-a) - k^(1-a), b_0 = 1.  v1 used b_1..b_n, so the newest
%     increment carried b_1 = 2^(1-a)-1 instead of 1; at a = 1 the whole
%     damping term vanished.
%
%  3. TIME STEPPING.  Newmark (beta=1/4, gamma=1/2) with the L1 term
%     implicit.  Unconditionally stable for the mechanical part; v1 used an
%     explicit central difference with a heuristic stability warning.
%
%  4. POLING / ELECTRODES.  p.poling and p.electrodes are independent
%     switches.  A homogeneous plate with through-thickness electrodes
%     carries no net charge in pure bending, so k_eff^2 ~ 0 there; use
%     poling 'x' with left/right electrodes (length extension) if a
%     voltage is wanted.
%
%  5. MATERIAL.  p.material = 'fem5' uses the tetragonal BaTiO3 data of
%     FEM-5 with the correct anisotropy ratio k11/k33 = 39; 'placeholder'
%     reproduces the isotropic-C data of v1.
%
% Self-tests are printed first; all of them must pass before the numbers
% are used.

clear; clc; close all;

%% ---------------------------- input ----------------------------
p.Lx = 200e-6;  p.Ly = 10e-6;  p.th = 10e-6;   % m
p.nelx = 24;    p.nely = 2;
p.bc = "clamped_free";        % "bridge" | "clamped_free"
p.material = "fem5";          % "fem5" | "placeholder"
p.poling = "x";               % "x" | "y"
p.electrodes = "lr";          % "lr" | "tb"
p.rho = 6020;                 % kg/m^3

p.domain = "cuboid";          % "cuboid" | "ellipsoid"
p.ax = 3e-6;  p.ay = 1e-6;    % half-widths / semi-axes
p.theta = 0;                  % rad

nm = 8;                       % retained modes
alpha_list = [1.0 0.9 0.7];
tau  = 3e-7;                  % s
u0   = 10e-9;                 % initial mid-span displacement (m)
T    = 8*2*pi/7.161e6;        % ~8 periods of the axial mode (s)
Nt   = 8000;  dt = T/Nt;

%% ---------------------------- model ----------------------------
[Ro, Mo] = solve_modes(p, "open",  nm);
[Rs, Mo2] = solve_modes(p, "short", nm);
fo = Ro.omega/2/pi;  fs = Rs.omega/2/pi;
k2 = (Ro.omega.^2 - Rs.omega.^2)./Ro.omega.^2;
[~, jax] = max(k2);

fprintf('\n=========== FEM-6 v2 ===========\n');
fprintf('domain=%s  poling=%s  electrodes=%s  material=%s  bc=%s\n', ...
        p.domain, p.poling, p.electrodes, p.material, p.bc);
fprintf('ndof(mech, condensed) = %d,  modes kept = %d\n', size(Mo,1), nm);
for k = 1:nm
    fprintf('  mode %d: f_open = %9.4f kHz  f_short = %9.4f kHz  k_eff^2 = %+.4f\n', ...
            k, fo(k)/1e3, fs(k)/1e3, k2(k));
end
fprintf('largest k_eff^2 in mode %d (%.4f kHz, k^2 = %.4f)\n', ...
        jax, fo(jax)/1e3, k2(jax));

%% ---------------------------- self-tests ----------------------------
fprintf('\n--- self-tests (must all pass) ---\n');
fprintf('capacitance       %+.6e F   analytic %+.6e F   rel.err %.2e  %s\n', ...
        Ro.beta, Ro.beta_analytic, abs(Ro.beta/Ro.beta_analytic-1), ...
        pass(abs(Ro.beta/Ro.beta_analytic-1) < 1e-6));
dK = eig(full(Ro.Keff - Rs.Keff)); dK = dK/max(abs(dK));
fprintf('min eig(Koc-Ksc)  %+.3e   (>= 0 required)   %s\n', min(real(dK)), ...
        pass(min(real(dK)) > -1e-9));
eK = eig(full(Rs.Keff)); eK = eK/max(abs(eK));
fprintf('min eig(Ksc)      %+.3e   (>  0 required)   %s\n', min(real(eK)), ...
        pass(min(real(eK)) > 0));
fprintf('static deflection direct %.6e m | modal(%d) %.6e m | rel.diff %.2e  %s\n', ...
        Ro.u_static_direct, nm, Ro.u_static_modal, ...
        abs(Ro.u_static_modal/Ro.u_static_direct-1), ...
        pass(abs(Ro.u_static_modal/Ro.u_static_direct-1) < 0.15));
fprintf('electrode charge of mode 1 (open) %.3e C\n', abs(Ro.V(1)));

%% ---------------------- memory: complex pole ----------------------
fprintf('\ncomplex pole of mode %d, tau = %.2e s, tau*omega = %.3f\n', ...
        jax, tau, tau*Ro.omega(jax));
fprintf('  alpha    f_d (kHz)     zeta\n');
for a = alpha_list
    s = cplx_root(Ro.omega(jax), tau, a);
    fprintf('   %.2f    %9.4f    %.6e\n', a, imag(s)/2/pi/1e3, -real(s)/abs(s));
end

%% ------------------------ time response ------------------------
q0 = zeros(nm,1);  q0(jax) = u0/Ro.midshape(jax);
f  = zeros(nm,1);  f(jax) = 1;                 % unit modal force
t  = (0:Nt)*dt;

fig = figure('Color','w','Position',[100 100 900 680]);
for a = alpha_list
    q  = modal_fractional_newmark(Ro.omega, f, tau, a, dt, Nt, q0);
    um = Ro.midshape*q;  V = Ro.V*q;
    subplot(2,1,1); hold on; plot(t*1e6, um*1e9, 'LineWidth',1.3, ...
        'DisplayName', sprintf('\\alpha = %.1f',a));
    subplot(2,1,2); hold on; plot(t*1e6, V,     'LineWidth',1.3, ...
        'DisplayName', sprintf('\\alpha = %.1f',a));
    fprintf('alpha %.1f: peak |u| %.4f nm, peak |V| %.4f V, value at t_end %.3e\n', ...
            a, max(abs(um))*1e9, max(abs(V)), V(end));
end
subplot(2,1,1); grid on; box on; xlabel('t (\mus)'); ylabel('u_{mid} (nm)');
legend('show','Location','northeast'); title('(a) displacement');
subplot(2,1,2); grid on; box on; xlabel('t (\mus)'); ylabel('V_{oc} (V)');
legend('show','Location','northeast'); title('(b) open-circuit voltage');
print(fig, 'FEM6_v2_memory.png', '-dpng', '-r200');

%% ---------------------- orientation sweep ----------------------
fprintf('\n--- orientation sweep (cuboid, a_x=%.1e, a_y=%.1e) ---\n', p.ax, p.ay);
fprintf(' theta   f1(kHz)   k2(mode1)   k2(axial)   f_axial(kHz)\n');
for th = [0 30 60 90]
    pp = p;  pp.theta = th*pi/180;
    A1 = solve_modes(pp,"open",nm);  A2 = solve_modes(pp,"short",nm);
    kk = (A1.omega.^2 - A2.omega.^2)./A1.omega.^2;
    [~, jj] = max(kk);
    fprintf('  %3d    %8.4f   %.3e   %+.4f     %9.4f\n', th, ...
            A1.omega(1)/2/pi/1e3, kk(1), kk(jj), A1.omega(jj)/2/pi/1e3);
end

%% ---------------------- domain comparison ----------------------
fprintf('\n--- cuboid vs ellipsoid at equal second moment ---\n');
fprintf('  domain      f1(kHz)    f_axial(kHz)   k2(axial)\n');
cfgs = {"cuboid",3e-6,1e-6; "ellipsoid",3e-6*sqrt(3/5),1e-6*sqrt(3/5); ...
        "ellipsoid",3e-6,1e-6; "cuboid",3e-6*sqrt(5/3),1e-6*sqrt(5/3)};
for c = 1:size(cfgs,1)
    pp = p;  pp.domain = cfgs{c,1};  pp.ax = cfgs{c,2};  pp.ay = cfgs{c,3};
    A1 = solve_modes(pp,"open",nm);  A2 = solve_modes(pp,"short",nm);
    kk = (A1.omega.^2 - A2.omega.^2)./A1.omega.^2;
    [~, jj] = max(kk);
    fprintf('  %-10s  %8.4f   %9.4f     %+.4f\n', cfgs{c,1}, ...
            A1.omega(1)/2/pi/1e3, A1.omega(jj)/2/pi/1e3, kk(jj));
end

%% ========================= local functions =========================
function s = pass(ok)
    if ok, s = "PASS"; else, s = "FAIL"; end
end

function [R, Mred] = solve_modes(p, circuit, nm)
    npn = 12; nelx = p.nelx; nely = p.nely;
    nnx = nelx+1; nny = nely+1; nnode = nnx*nny; ndof = npn*nnode;
    xg = linspace(0,p.Lx,nnx); yg = linspace(0,p.Ly,nny);
    nid = @(ix,iy) (iy-1)*nnx + ix;
    coords = zeros(nnode,2);
    for iy = 1:nny
        for ix = 1:nnx
            coords(nid(ix,iy),:) = [xg(ix), yg(iy)];
        end
    end
    conn = zeros(nelx*nely,4);  e = 0;
    for ey = 1:nely
        for ex = 1:nelx
            e = e+1;
            conn(e,:) = [nid(ex,ey) nid(ex+1,ey) nid(ex+1,ey+1) nid(ex,ey+1)];
        end
    end

    [C, epz, kap] = material_2d(p);
    cs = cos(p.theta); sn = sin(p.theta); Rm = [cs -sn; sn cs];
    switch p.domain
        case "cuboid",    Mg = Rm*diag([p.ax^2/3, p.ay^2/3])*Rm';
        case "ellipsoid", Mg = Rm*diag([p.ax^2/5, p.ay^2/5])*Rm';
        otherwise, error('p.domain must be "cuboid" or "ellipsoid"');
    end

    Kuu = sparse(ndof,ndof); Kup = sparse(ndof,ndof);
    Aem = sparse(ndof,ndof); Mss = sparse(ndof,ndof); F = zeros(ndof,1);
    [gp,gw] = gauss_1d_01(4);
    for e = 1:size(conn,1)
        nodes = conn(e,:); xy = coords(nodes,:);
        hx = xy(2,1)-xy(1,1); hy = xy(4,2)-xy(1,2);
        Kuue = zeros(32); Kupe = zeros(32,16); Ae = zeros(16);
        Me = zeros(32); Fe = zeros(32,1);
        for ig = 1:4
            for jg = 1:4
                [N,Nx,Ny,Nxx,Nyy,Nxy] = bfs_shape_2d(gp(ig),gp(jg),hx,hy);
                [B,Bx,By,Nv] = make_B_matrices(N,Nx,Ny,Nxx,Nyy,Nxy);
                w = gw(ig)*gw(jg)*hx*hy*p.th;
                Kg = 0.5*( Mg(1,1)*(Bx'*C*Bx) ...
                         + Mg(1,2)*(Bx'*C*By + By'*C*Bx) ...
                         + Mg(2,2)*(By'*C*By) );
                Kuue = Kuue + (B'*C*B + Kg)*w;
                G    = [Nx; Ny];
                Kupe = Kupe + B'*epz'*G*w;
                Ae   = Ae   + G'*kap*G*w;
                Me   = Me   + p.rho*(Nv'*Nv)*w;
                Fe   = Fe   + Nv'*[0;-1]*w;         % unit transverse load
            end
        end
        em = zeros(1,32); ep = zeros(1,16);
        for a = 1:4
            base = (nodes(a)-1)*npn;
            em((a-1)*8+(1:8)) = base+(1:8);
            ep((a-1)*4+(1:4)) = base+(9:12);
        end
        Kuu(em,em) = Kuu(em,em) + Kuue;
        Kup(em,ep) = Kup(em,ep) + Kupe;
        Aem(ep,ep) = Aem(ep,ep) + Ae;
        Mss(em,em) = Mss(em,em) + Me;
        F(em)      = F(em) + Fe;
    end

    % ------------------------- boundary conditions -------------------------
    left  = nid(1,1:nny);
    right = nid(nnx,1:nny);
    bot   = nid(1:nnx,1);
    top   = nid(1:nnx,nny);
    cl = left;  if p.bc == "bridge", cl = [left right]; end
    fixed = [];
    for n = cl
        fixed = [fixed, (n-1)*npn + (1:8)];                %#ok<AGROW>
    end
    if p.electrodes == "lr"
        eG = left;  eF = right;
        fixed = [fixed, (eG-1)*npn+9, (eG-1)*npn+11, (eF-1)*npn+11];
    else
        eG = bot;   eF = top;
        fixed = [fixed, (eG-1)*npn+9, (eG-1)*npn+10, (eF-1)*npn+10];
    end
    topphi = (eF-1)*npn + 9;
    if circuit == "short"
        fixed = [fixed, topphi];  master = [];  slaves = [];
    else
        master = topphi(1);  slaves = topphi(2:end);
    end
    fixed = unique(fixed);
    retained = setdiff(1:ndof, [fixed slaves]);  nred = numel(retained);
    colOf = zeros(1,ndof);  colOf(retained) = 1:nred;
    rows = [retained(:); slaves(:)];
    cols = [(1:nred)'; repmat(colOf(master), numel(slaves), 1)];
    P = sparse(rows, cols, 1, ndof, nred);

    isph = mod(retained-1, npn) >= 8;
    Pm = P(:,~isph);  Pp = P(:,isph);
    Kuur = full(Pm'*Kuu*Pm);  Kupr = full(Pm'*Kup*Pp);
    Ar = full(Pp'*Aem*Pp);    Mr = full(Pm'*Mss*Pm);  Fr = Pm'*F;

    % condense the potential dofs (scaled for conditioning)
    Sp = 1./sqrt(diag(Ar));
    As = (Sp*Sp').*Ar;
    Z  = Sp.*(As\(Sp.*Kupr'));
    Keff = Kuur + Kupr*Z;  Keff = (Keff+Keff')/2;

    % scaled symmetric eigenproblem (FEM-1 mass scaling)
    S  = 1./sqrt(abs(diag(Keff)));
    Ks = (S*S').*Keff;  Ms = (S*S').*Mr;
    [Vy,D] = eigs(Ks, Ms, nm, 'smallestabs');
    [lam,ix] = sort(real(diag(D)));  Vy = Vy(:,ix);
    for k = 1:nm
        Vy(:,k) = Vy(:,k)/sqrt(Vy(:,k)'*Ms*Vy(:,k));
    end
    Phi = S.*Vy;
    R.omega = sqrt(lam);

    % outputs
    ret_u = retained(~isph);
    mid = nid(round((nnx+1)/2), round((nny+1)/2));  vdof = (mid-1)*npn+5;
    iu = find(ret_u == vdof, 1);
    R.midshape = Phi(iu,:);
    R.fn = Phi'*Fr;
    if circuit == "open"
        Pot = Z*Phi;
        im = find(retained(isph) == master, 1);
        R.V = Pot(im,:);
    else
        R.V = zeros(1,nm);
    end
    ust = Keff\Fr;
    R.u_static_direct = ust(iu);
    R.u_static_modal  = sum(R.midshape(:).*R.fn(:)./R.omega(:).^2);
    R.Keff = Keff;

    % electrode capacitance: grounded electrode + interior value dofs
    % eliminated; the electrode nodes are tied to one potential
    tt = (eF-1)*npn+9;  gg = (eG-1)*npn+9;
    ifc = (setdiff(1:nnode,[eF eG])-1)*npn+9;
    Kc  = full(Aem([tt gg ifc],[tt gg ifc]));
    nt = numel(tt);  ng = numel(gg);
    Kii = Kc(nt+ng+1:end, nt+ng+1:end);
    Kti = Kc(1:nt, nt+ng+1:end);
    C1  = Kc(1:nt,1:nt) - Kti*(Kii\Kti');
    R.beta = sum(sum(C1));
    if circuit ~= "open", R.beta = NaN; end
    if p.electrodes == "lr"
        R.beta_analytic = kap(1,1)*p.Ly/p.Lx;
    else
        R.beta_analytic = kap(2,2)*p.Lx/p.Ly;
    end
    Mred = Mr;
end

function q = modal_fractional_newmark(w, f, tau, alpha, dt, Nt, q0)
% q'' + w.^2 (q + tau^alpha * D^alpha q) = f,  Newmark + L1 (implicit).
    nm = numel(w);  w = w(:);  f = f(:);
    w2 = w.^2;
    beta = 0.25;  gam = 0.5;
    c = dt^(-alpha)/gamma(2-alpha);
    k = 0:Nt;  b = (k+1).^(1-alpha) - k.^(1-alpha);   % b(1) = b_0 = 1
    A = 1 + beta*dt^2*(1+c)*w2;                        % diagonal (Kd = K)
    q = zeros(nm,Nt+1);  v = q;  a = q;  dq = zeros(nm,Nt);
    q(:,1) = q0;
    a(:,1) = f - w2.*q0;
    for n = 1:Nt
        yhat = q(:,n) + dt*v(:,n) + dt^2*(0.5-beta)*a(:,n);
        S = zeros(nm,1);
        if n >= 2
            S = dq(:,n-1:-1:1)*b(2:n)';      % sum_{k=1}^{n-1} b_k dq_{n-k}
        end
        rhs = f - w2.*(1+c).*yhat + c*w2.*(q(:,n) - S);
        an  = rhs./A;
        q(:,n+1) = yhat + beta*dt^2*an;
        v(:,n+1) = v(:,n) + dt*((1-gam)*a(:,n) + gam*an);
        a(:,n+1) = an;
        dq(:,n)  = q(:,n+1) - q(:,n);
    end
end

function s = cplx_root(w, tau, alpha)
    s = w*(-0.05 + 1i);
    for it = 1:200
        fv  = s^2 + w^2*(1 + (tau*s)^alpha);
        dfv = 2*s + w^2*alpha*tau^alpha*s^(alpha-1);
        ds  = fv/dfv;
        s   = s - ds;
        if abs(ds) < 1e-14*abs(s), break; end
    end
end

function [C, epz, kap] = material_2d(p)
    if p.material == "fem5"
        C11 = 2.22e11; C12 = 1.08e11; C13 = 1.11e11; C33 = 1.51e11; C44 = 6.10e10;
        e31 = -0.7; e33 = 6.7; e15 = 34.2;
        k11 = 1.9479e-8; k33 = 4.9583e-10;
    else
        E = 100e9; nu = 0.30;
        lam = E*nu/((1+nu)*(1-2*nu)); mu = E/(2*(1+nu));
        C11 = lam+2*mu; C12 = lam; C13 = lam; C33 = lam+2*mu; C44 = mu;
        e31 = -4.4; e33 = 18.6; e15 = 11.6;
        k11 = 1.2e-8; k33 = 1.0e-8;
    end
    if p.poling == "y"
        C   = [C11 C13 0; C13 C33 0; 0 0 C44];
        epz = [0 0 e15; e31 e33 0];
        kap = diag([k11 k33]);
    elseif p.poling == "x"
        C   = [C33 C13 0; C13 C11 0; 0 0 C44];
        epz = [e33 e31 0; 0 0 e15];
        kap = diag([k33 k11]);
    else
        error('p.poling must be "x" or "y"');
    end
end

function [gp,gw] = gauss_1d_01(n)
    if n ~= 4, error('Only n=4 implemented.'); end
    x = [-0.8611363115940526, -0.3399810435848563, ...
          0.3399810435848563,  0.8611363115940526];
    w = [ 0.3478548451374538,  0.6521451548625461, ...
          0.6521451548625461,  0.3478548451374538];
    gp = (x+1)/2;  gw = w/2;
end

function [N, Nx, Ny, Nxx, Nyy, Nxy] = bfs_shape_2d(s,t,hx,hy)
    [Hx0,Hx1,Hx0x,Hx1x,Hx0xx,Hx1xx] = hermite_1d_two_nodes(s,hx);
    [Hy0,Hy1,Hy0y,Hy1y,Hy0yy,Hy1yy] = hermite_1d_two_nodes(t,hy);
    xs = [1 2 2 1];  ys = [1 1 2 2];
    N = zeros(1,16);  Nx = N;  Ny = N;  Nxx = N;  Nyy = N;  Nxy = N;
    for a = 1:4
        ix = xs(a);  iy = ys(a);  pp = (a-1)*4;
        N(pp+1)   = Hx0(ix)*Hy0(iy);
        Nx(pp+1)  = Hx0x(ix)*Hy0(iy);
        Ny(pp+1)  = Hx0(ix)*Hy0y(iy);
        Nxx(pp+1) = Hx0xx(ix)*Hy0(iy);
        Nyy(pp+1) = Hx0(ix)*Hy0yy(iy);
        Nxy(pp+1) = Hx0x(ix)*Hy0y(iy);
        N(pp+2)   = Hx1(ix)*Hy0(iy);
        Nx(pp+2)  = Hx1x(ix)*Hy0(iy);
        Ny(pp+2)  = Hx1(ix)*Hy0y(iy);
        Nxx(pp+2) = Hx1xx(ix)*Hy0(iy);
        Nyy(pp+2) = Hx1(ix)*Hy0yy(iy);
        Nxy(pp+2) = Hx1x(ix)*Hy0y(iy);
        N(pp+3)   = Hx0(ix)*Hy1(iy);
        Nx(pp+3)  = Hx0x(ix)*Hy1(iy);
        Ny(pp+3)  = Hx0(ix)*Hy1y(iy);
        Nxx(pp+3) = Hx0xx(ix)*Hy1(iy);
        Nyy(pp+3) = Hx0(ix)*Hy1yy(iy);
        Nxy(pp+3) = Hx0x(ix)*Hy1y(iy);
        N(pp+4)   = Hx1(ix)*Hy1(iy);
        Nx(pp+4)  = Hx1x(ix)*Hy1(iy);
        Ny(pp+4)  = Hx1(ix)*Hy1y(iy);
        Nxx(pp+4) = Hx1xx(ix)*Hy1(iy);
        Nyy(pp+4) = Hx1(ix)*Hy1yy(iy);
        Nxy(pp+4) = Hx1x(ix)*Hy1y(iy);
    end
end

function [H0,H1,H0x,H1x,H0xx,H1xx] = hermite_1d_two_nodes(s,L)
    h1 = 1 - 3*s^2 + 2*s^3;   h2 = L*(s - 2*s^2 + s^3);
    h3 = 3*s^2 - 2*s^3;       h4 = L*(-s^2 + s^3);
    dh1 = -6*s + 6*s^2;       dh2 = L*(1 - 4*s + 3*s^2);
    dh3 =  6*s - 6*s^2;       dh4 = L*(-2*s + 3*s^2);
    d2h1 = -6 + 12*s;         d2h2 = L*(-4 + 6*s);
    d2h3 =  6 - 12*s;         d2h4 = L*(-2 + 6*s);
    H0 = [h1 h3];    H1 = [h2 h4];
    H0x  = (1/L)*[dh1 dh3];    H1x  = (1/L)*[dh2 dh4];
    H0xx = (1/L^2)*[d2h1 d2h3]; H1xx = (1/L^2)*[d2h2 d2h4];
end

function [B,Bx,By,Nv] = make_B_matrices(N,Nx,Ny,Nxx,Nyy,Nxy)
    B = zeros(3,32);  Bx = B;  By = B;  Nv = zeros(2,32);
    for a = 1:4
        sp = (a-1)*4 + (1:4);
        up = (a-1)*8 + (1:4);
        vp = (a-1)*8 + (5:8);
        Nv(1,up) = N(sp);    Nv(2,vp) = N(sp);
        B(1,up) = Nx(sp);    B(2,vp) = Ny(sp);
        B(3,up) = Ny(sp);    B(3,vp) = Nx(sp);
        Bx(1,up) = Nxx(sp);  Bx(2,vp) = Nxy(sp);
        Bx(3,up) = Nxy(sp);  Bx(3,vp) = Nxx(sp);
        By(1,up) = Nxy(sp);  By(2,vp) = Nyy(sp);
        By(3,up) = Nyy(sp);  By(3,vp) = Nxy(sp);
    end
end
