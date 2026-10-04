"""Original continuous cotton-shirt cross sections. No external geometry."""
from math import sqrt, sin, exp, log
SLEEVE = [(-.14,1.88,.286,.306),(.35,1.92,.30,.313),(1.04,1.93,.313,.323),(1.65,1.87,.32,.33),(2.13,1.70,.32,.33),(2.32,1.52,.23,.26),(2.44,1.40,.018,.030)]

def create_garment_surface(torso, interpolate, gaussian):
    def width(z):
        result=interpolate(torso,z)
        if z<2.44:
            result=max(result,interpolate(SLEEVE,z)+interpolate(SLEEVE,z,2))
        return result

    def surface(x,z,front=True):
        w=interpolate(torso,z)
        fr=interpolate(torso,z,2)
        ba=interpolate(torso,z,3)
        candidates=[]
        if abs(x)<=w+.000001:
            cy=(fr+ba)/2
            depth=(ba-fr)/2*sqrt(max(0,1-(x/w)**2))
            y=cy-depth if front else cy+depth
            if front:
                for sign in (-1,1):
                    y-=.075*gaussian(x,z,sign*.63,1.26,.54,.64)
                y+=.012*gaussian(x,z,0,1.15,.15,.70)
                y-=.026*gaussian(x,z,0,2.47,.66,.38)
                for button_z in (1.58,.83,.08):
                    distance=z-button_z-.19*abs(x)
                    y-=.010*exp(-(distance/.034)**2)*exp(-(x/.50)**2)
                y-=.009*sin(13*z+4*x)*exp(-((abs(x)-.36)/.23)**2)
                y-=.007*sin(19*z+3*x)*exp(-((z-.3)/.27)**2)
            candidates.append(y)
        if z<2.44:
            center=interpolate(SLEEVE,z)
            rx=interpolate(SLEEVE,z,2)
            ry=interpolate(SLEEVE,z,3)
            for sign in (-1,1):
                q=(x-sign*center)/max(.001,rx)
                if abs(q)<=1.00001:
                    depth=ry*sqrt(max(0,1-q*q))
                    y=.075-depth if front else .075+depth
                    fold=.007*sin(13*z+4*q)*exp(-((z-1.4)/.9)**2)
                    candidates.append(y-fold if front else y+fold)
        if not candidates:
            return (fr+ba)/2
        base=min(candidates) if front else max(candidates)
        direction=-1 if front else 1
        return base+direction*.015*log(sum(exp(direction*(value-base)/.015) for value in candidates))
    return width, surface
