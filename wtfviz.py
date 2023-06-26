import wtfutil
import colorsys
import cubehelix
import numpy as np
import math


def gcolor(n):
    def to_rgb(hsl):
        return colorsys.hls_to_rgb(hsl[0]/360, hsl[2], hsl[1])
    
    bases =[
        [(240,.35,.35),(240,.65,.60),(240,.35,.75)],
        [(80,.35,.35),(80,.55,.45),(80,.35,.75)],
        [(40,.35,.35),(45,.75,.45),(40,.35,.75)],
        [(0,.35,.35),(0,.65,.55),(0,.35,.75)],
        [(300,.35,.35),(300,.65,.50),(300,.35,.75)],
    ]
    [under, excess] = [(0,.0,.35), (0,.0,.85)]
    
    # normalize
    n = round(n*1000)/1000
    
    n = n*10.0
    
    if n < 0:
        return to_rgb(under)
    
    if n >= 10.0:
        return to_rgb(excess)
    
    cat = int(n//2)
    sub = (n)%1
    if n/2%1 < 0.5:
        a = bases[cat][0]
        b = bases[cat][1]
    else:
        a = bases[cat][1]
        b = bases[cat][2]

    ca = 1-sub
    cb = sub
    
    final = (
        ca * a[0] + cb * b[0],
        ca * a[1] + cb * b[1],
        ca * a[2] + cb * b[2]
    )
    return to_rgb(final)



def fn_apply_colorize(idx, reverse=True, cmap='gcolor'):
    HIGHEST=800
    if np.isnan(idx):
        return ''
    if reverse:
        idx = np.round(np.log(idx)*100)
    
    
    ch = cubehelix.cmap(minLight=.15,maxLight=.95,minSat=0,maxSat=0)
    if cmap == 'ch1':
        ch = cubehelix.cmap(minLight=.15,maxLight=.95)
    elif cmap == 'ch2':
        ch = cubehelix.cmap(startHue=240,endHue=-300,minSat=1,maxSat=2.5,minLight=.3,maxLight=.8,gamma=.9)
    elif cmap == 'gcolor':
        ch = gcolor
    
    color = ch(idx/HIGHEST)
    fill = f'rgb({color[0]*256:.0f},{color[1]*256:.0f},{color[2]*256:.0f})'
            
    return '''
    1font-size: 15px;
    text-shadow: 0px 0px 2px rgba(0, 0, 0, 1), 0px 0px 0.5px rgba(0, 0, 0, 1);
    min-width: 60px;
    color: rgba(255, 255, 255, .99);
    1font-weight: 8000;
    background: ''' + fill


class CBar():
    el = []
    
    def __init__(self, series, stop=1.0, start=0.0, ticks=5, cmap='gcolor', wmod=0, h=90, m=900, bg=(0.95,0.95,0.95)):
        el = list()
        
        HIGHEST = 800
        
        el.append(f'<svg width="{m}" height="{h}" xmlns="http://www.w3.org/2000/svg">')
        
        # background
        color = bg
        fill = f'rgb({color[0]*256:.0f},{color[1]*256:.0f},{color[2]*256:.0f})'
        d = f'M {0} {0} L {0} {h} L {m} {h} L {m} 0 Z'
        el.append(f'<path d="{d}"fill="{fill}" stroke-dasharray="5,5" stroke-width="0.5" stroke="grey"/>')
        
        # mine the start
        amine = wtfutil.mine_series(series, start)[1]
        
        # mine until stop
        amine = wtfutil.mine_series(amine, stop-start)[0]
        
        ch = cubehelix.cmap(minLight=.15,maxLight=.95,minSat=0,maxSat=0)
        if cmap == 'ch1':
            ch = cubehelix.cmap(minLight=.15,maxLight=.95)
        elif cmap == 'ch2':
            ch = cubehelix.cmap(startHue=240,endHue=-300,minSat=1,maxSat=2.5,minLight=.3,maxLight=.8,gamma=.9)
        elif cmap == 'gcolor':
            ch = gcolor
        
        # calculate the ratio
        ratio = m/(stop-start)
        start = 0.0
        
        min_width = math.ceil(h/200)
        max_width = h
        
        for idx, val in zip(series.index, amine):
            
            # determine thickness
            
            if 0:
                pass
            elif wmod == 1:
                width = (max_width-min_width)/HIGHEST * idx + min_width
                width = idx / HIGHEST * 0.96 + 0.04
                width *= max_width #

            elif wmod == 2:
                width = (max_width-min_width)/np.exp(HIGHEST/100) * np.exp(idx/100) + min_width
            elif wmod == 3:
                min_width = 0
                width = math.sqrt(np.exp(idx/100))/math.sqrt(np.exp(HIGHEST/100)) * (max_width-min_width) + min_width
            else:
                width = max_width

            
            # TODO: calculate wmod4: dh/dV using pi
            
            if val == 0.0:
                continue

            color = ch(idx/HIGHEST)
            fill = f'rgb({color[0]*256:.0f},{color[1]*256:.0f},{color[2]*256:.0f})'
            x0 = math.floor(start)
            x1 = math.ceil(start + ratio*val)
            y0 = math.floor((h - width) / 2)
            y1 = math.ceil((h + width) / 2)
            
            d = f'M {x0} {y0} L {x0} {y1} L {x1} {y1} L {x1} {y0} Z'            
            el.append(f'<path d="{d}" fill="{fill}"/>')
            start += ratio*val
        
        for i in range(1,ticks):
            el.append(f'<line x1="{i*m/ticks}" y1="0" x2="{i*m/ticks}" y2="{h}" stroke-dasharray="5,5" stroke-width="1" stroke="rgba(128,128,128,0.25)"/>')
            
        el.append(f'</svg>')
    
        self.el = el
        
    
    def _repr_html_(self):
        return ''.join(self.el)
