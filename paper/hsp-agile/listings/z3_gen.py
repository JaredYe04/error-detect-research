solver = z3.Solver()
solver.add(phi_i)           # phi_i is the Z3 formula for Phi_i
if solver.check() == z3.sat:
    model = solver.model()
    concrete = {v: model[v].as_long() for v in z3_vars}
    D.append(concrete)
