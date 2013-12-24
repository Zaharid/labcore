# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 16:47:33 2013

@author: zah
"""

import numpy as np

from pqdict import PQDict
atan2 = np.arctan2
pi = np.pi
class AdaptiveSampler(object):
    def __init__(self, f, a ,b, sample_over = None, 
                 min_angle =  0.1, init_points = 7, 
                 epsilon = 0, max_points = 700,
                 yscale = None, measure_at = None, scalefactor = 5,
                 min_delta = 1e-3):
        
        self.f = f
        self.a = a
        self.b = b
        self.sample_over = sample_over
        self.init_points = init_points
        self.min_angle = min_angle
        self.epsilon = epsilon
        if max_points < 3:
            raise ValueError('max_points must be at least three')
        self.max_points = max_points
        self.yscale = yscale
        self.scalefactor = scalefactor        
        self.measure_at = measure_at    
        self.min_delta = min_delta
        
        self.scale_to_x = lambda x: a + x*(b-a)
        
        
    
    
    def get_prior(self, x, y ,xp, yp, xn, yn):
        a1 = atan2(y-yp,x-xp + self.epsilon)
        a2 = atan2(yn-y,xn-x + self.epsilon)
        prior = -(min(np.abs(a1-a2), 2*pi-np.abs((a1-a2))))
        return prior
    
    
    def getf(self, x):
        xret = self.scale_to_x(x)
        
        yret = self.f(xret)
        y = self.scale_from_y(self.get_y(yret))
        return xret, yret, y
    
    def get_y(self,yret):
        if self.sample_over is not None:
            return yret[self.sample_over]
        else:
            return yret
        
        
    def evalx(self, x, y, xp, yp, xn, yn):
        
        lx = (x+xp)/2.
        rx = (xn+x)/2.
        
        lxret, lyret, ly = self.getf(lx)
        yield lxret, lyret
        
        rxret, ryret, ry = self.getf(rx)
        yield rxret, ryret
        
        ldata = [ly, xp, yp, x, y]
        rdata = [ry, x, y, xn, yn]
        
        self.update_data(lx, ldata)
        self.update_data(rx, rdata)
        
        try:
            xpd = self.data[xp]
        except KeyError:
            pass
        else:
            xpd[3] = lx
            xpd[4] = ly
            self.update_data(xp, xpd)
        try:
            xnd = self.data[xn]
        except KeyError:
            pass
        else:
            xnd[1] = rx
            xnd[2] = ry
            self.update_data(xn, xnd)
        
        xd = [y, lx, ly, rx, ry]
        self.update_data(x, xd)
        
    
    def update_data(self, x, data):
        prior = self.get_prior(x, *data)
        mind = min((x-data[1], data[3]-x))
        if -prior > self.min_angle and self.min_delta < mind:
            self.data[x] = data
            self.heapdict[x] = prior
        elif x in self.data:
            del self.data[x]
            del self.heapdict[x]

    
    
        

    def run(self):
        self.heapdict = PQDict()
        self.data = {}
        initx = np.linspace(0, 1, self.init_points)
        if self.measure_at is not None:
            xm = [(x-self.a)/(self.b-self.a) for x in self.measure_at]    
            initx = np.concatenate((initx, xm))
            initx.sort()
            
        #initdelta = (initx[1] - initx[0])/2.
        inity = []
        for x in initx:
            xret = self.scale_to_x(x)
            yret = self.f(xret)
            yield (xret, yret)
           
            inity.append(self.get_y(yret))
            
        if self.yscale is None:
            self.yscale = max(inity)-min(inity)
            
        #self.scale_from_y = lambda y: (y-min(inity))/(max(inity)-min(inity)) 
        self.scale_from_y = lambda y: (y) / self.yscale / self.scalefactor
        inity = [self.scale_from_y(y) for y in inity]

        for (i, x) in enumerate(initx[1:-1],1):
            d = [inity[i], 
                 initx[i-1], inity[i-1], 
                 initx[i+1], inity[i+1]]
            
            self.update_data(x, d)
        
        n_points = self.init_points
        while n_points < self.max_points:
            try:
                x = self.heapdict.top()
                
            except KeyError:
                return
            else:
                d = self.data[x]
                for point in self.evalx(x, *d): yield point
                n_points += 2
                
    def __call__(self):
        return self.run()
        
        
        
        
        
def test(**kwargs):
    global s, it, x, y
    from scipy import stats
    import matplotlib.pyplot as plt
    from matplotlib import animation
    
    

    f = lambda x :  stats.cauchy.pdf(x,0.73,.3) + stats.cauchy.pdf(x,4.7,.1)
    fig = plt.figure()
    ax = plt.axes(xlim=(-6, 6), ylim=(-0, 4.1))
    x = []
    y = []
    line, = ax.plot(x, y, 'o',lw=2)
    
    
    def init():
        global s, it, x, y
        s = AdaptiveSampler(f, -4, 5.1, **kwargs)
        it = s.run()
        x = []
        y = []
        line.set_data([], [])
        return line,
    
    def animate(i):
        point = next(it)
        x.append(point[0])
        y.append(point[1])
        line.set_data(x,y)
        return line,
    anim = animation.FuncAnimation(fig, animate, init_func = init,
                                   frames=80, interval=100, blit=True, 
                                   )
    plt.show()
    plt.plot(x,y, marker = 'o', drawstyle = 'steps')
    plt.plot(sorted(x),f(sorted(x)))
    mx = np.linspace(np.min(x),np.max(x), 50000)
    plt.plot(mx,f(mx))
    plt.show()