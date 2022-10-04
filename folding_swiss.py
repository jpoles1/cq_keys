from cadquery import *

from dataclasses import dataclass
import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

from cq_warehouse.fastener import SocketHeadCapScrew
import cq_warehouse.extensions

@dataclass
class FoldingSwiss(StylishPart):
    seg_h: float = 25
    seg_w: float = 50
    seg_thick: float = 8
    hinge_thick = 3

    max_fold_angle: float = 60

    show_screws: bool = True

    def calc_vars(self):
        self.screw = SocketHeadCapScrew(size="M4-0.7", length=20, fastener_type="iso4762", simple=True)
    
    def make_seg(self, assembly, outer_seg=True): 
        #If inner_seg, this is the segment which is on the inside of the hinge. It is thinner as it does not need to accomodate the bolt head/nut
        hinge_cutout_thick = self.hinge_thick if outer_seg else self.seg_thick - self.hinge_thick
        hinge_cutout = (
            Workplane("XZ")#.workplane(offset=self.seg_h/2)
            .moveTo(self.seg_h/2,0)
            .rect(self.seg_w, hinge_cutout_thick, centered=[0,0])
            .revolve(self.max_fold_angle * 2, (0,0), (0,1))
            .rotate((0,0,0), (0,0,1), -self.max_fold_angle)
            .translate((-self.seg_h/2, 0, 0))
            .copyWorkplane(Workplane("XY"))
            .circle(self.seg_h/2).extrude(hinge_cutout_thick)
        )

        seg = (
            Workplane("XY").moveTo(self.seg_h/2-self.seg_w/2).rect(self.seg_w, self.seg_h)
            .extrude(self.seg_thick)
            .edges("|Z").fillet(self.seg_h/2-0.05)
            .cut(hinge_cutout)
        )
            
        if outer_seg:
            seg = (
                seg
                .faces(">Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.screw, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
                .moveTo(-self.seg_w + self.seg_h,0)
                .clearanceHole(fastener=self.screw, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
            )
        else:
            seg = (
                seg
                .faces(">Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.screw, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
                .faces("<Z").workplane()
                .moveTo(-self.seg_w + self.seg_h,0)
                .clearanceHole(fastener=self.screw, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=True)
            )
            seg = (
                seg.rotate((0,0,0), (0,1,0), 180)
                .translate((0,0,self.seg_thick))
            )            
            
        return seg

    def make(self):
        a = Assembly()
        a.add(self.make_seg(a))
        a.add(self.make_seg(a, False))
        print(a.fastenerQuantities())
        return a

if "show_object" in locals():
    FoldingSwiss(show_screws=0).display(show_object)
    #FoldingSwiss().display_split(show_object)
