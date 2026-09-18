"""PARAMETERS — fridge-magnet bag clip. Every dimension lives here; model.py has no literals."""

# --- jaws (printed open, end to end along X, hinge at x=0) ---
JAW_W = 20.0            # mm, jaw width (Y) = hinge width
JAW_LEN_UP = 84.0       # mm, upper jaw length from its hinge stub to the free end
CATCH_L = 6.0           # mm, the lower jaw is this much longer: the catch block lives there
JAW_LEN_LOW = JAW_LEN_UP + CATCH_L
JAW_T_UP = 2.4          # mm, upper jaw thickness (6 lines): the jaw that bows to snap under the lip
JAW_T_LOW = 3.2         # mm, lower jaw thickness: thick enough to bury 2 mm magnets with a 1.2 mm floor
CORNER_R = 4.0          # mm, plan-view corner radius on the free ends (hinge ends are covered by the hinge stubs)

# --- living hinge (mechanisms.living_hinge_web) ---
WEB_T = 0.5             # mm, one 0.4 mm line + a little: 2-3 layers when printed flat
WEB_LEN = 2.5           # mm, web span between the jaws
PANEL_LEN = 4.0         # mm, hinge stub panels (buried in the jaws); = CORNER_R so the stubs fill the rounded corners
PANEL_T = JAW_T_UP      # mm, the stubs are as thick as the thinner jaw; the lower jaw plate overlaps them
BAG_GAP = 0.4           # mm, room the folded web leaves between the jaw faces (the bag goes here)

# --- sealing rib: snap_ridge on the lower jaw meets snap_groove in the upper jaw through the bag ---
RIDGE_R = 0.6           # mm
RIDGE_LEN = JAW_LEN_UP - 16.0   # mm, stops 8 mm short of the hinge stub and of the free end
GROOVE_CLEAR = 0.3      # mm, groove radius over the ridge radius: room for two layers of bag film
UP_XC = WEB_LEN / 2 + JAW_LEN_UP / 2         # mm, upper jaw centre (x > 0)
LOW_XC = -(WEB_LEN / 2 + JAW_LEN_LOW / 2)    # mm, lower jaw centre (x < 0)
RIDGE_XC = -UP_XC                            # mm, the ridge sits under the folded upper jaw's centre

# --- catch: a block at the lower jaw's far end with an undercut the upper jaw's tip snaps into ---
TIP_X = -(WEB_LEN / 2 + JAW_LEN_UP)          # mm, where the upper jaw's free end lands when folded
TIP_CLEAR = 0.3         # mm, between the landed tip and the block's inner face
LIP_OVER = 0.8          # mm, undercut depth: how far the lip reaches over the tip
LIP_T = 1.6             # mm, lip thickness above the undercut
TIP_SLOP = 0.4          # mm, undercut height over the upper jaw thickness
CATCH_X_IN = TIP_X - TIP_CLEAR               # mm, inner (hinge-facing) face of the block
CATCH_X_OUT = -(WEB_LEN / 2 + JAW_LEN_LOW)   # mm, outer face = the lower jaw's end
CATCH_LEN = CATCH_X_IN - CATCH_X_OUT         # mm, block length (5.7)
NOTCH_Z0 = JAW_T_LOW + BAG_GAP - TIP_SLOP / 2    # mm, undercut floor
NOTCH_Z1 = NOTCH_Z0 + JAW_T_UP + TIP_SLOP        # mm, undercut roof = lip underside
CATCH_H = NOTCH_Z1 + LIP_T                       # mm, block height (8.0)
LIP_CHAMFER = LIP_T - 0.4                        # mm, 45 deg entry ramp on the lip's inner top edge

# --- thumb scoop in the upper jaw's free end (pushing here bows the jaw and frees the tip) ---
SCOOP_W = 12.0          # mm, leaves 4 mm of tip either side to latch under the lip
SCOOP_D = 3.5           # mm

# --- magnets in the lower jaw's bed face ---
MAGNET_D = 10.0         # mm, 10 x 2 disc magnets
MAGNET_H = 2.0
MAGNET_CLEAR = 0.3      # mm, glue fit
MAGNET_X = 25.0         # mm, either side of the lower jaw centre
assert JAW_T_LOW - MAGNET_H >= 1.2, "magnet pocket floor thinner than 3 layers"
