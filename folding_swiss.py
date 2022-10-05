from cadquery import *

from dataclasses import dataclass
import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

from cq_warehouse.fastener import SocketHeadCapScrew, HexNut
import cq_warehouse.extensions

@dataclass
class FoldingSwiss(StylishPart):
    seg_h: float = 25
    seg_w: float = 50
    seg_thick: float = 8
    hinge_thick = 3

    key_thick = 8

    max_fold_angle: float = 60

    show_screws: bool = True

    def calc_vars(self):
        self.screw = SocketHeadCapScrew(size="M4-0.7", length=20, fastener_type="iso4762", simple=True)
        self.nut = HexNut(size="M4-0.7", fastener_type="iso4032")
    
    def make_seg(self, assembly, outer_seg=True, bolt_half=True): 
        #If inner_seg, this is the segment which is on the inside of the hinge. It is thinner as it does not need to accomodate the bolt head/nut
        hinge_cutout_thick = self.hinge_thick if outer_seg else self.seg_thick - self.hinge_thick
        hinge_cutout = (
            Workplane("XZ")
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

        divot = (
            seg.faces("<Z[-2]").workplane()
            .moveTo(self.seg_h/4,0)
            .circle(1).extrude(1, combine=False)
            .faces("<Z").fillet(1-0.01)
        )

        seg = seg.union(divot)
        seg = seg.cut(divot.rotate((0,0,0), (0,0,1), 180).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(divot.rotate((0,0,0), (0,0,1), 180-(self.max_fold_angle-5)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(divot.rotate((0,0,0), (0,0,1), 180+(self.max_fold_angle-5)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))

        if not bolt_half:
            seg = seg.rotate((0,0,0), (1,0,0), 180).translate((0,0,-self.key_thick))
        if outer_seg:
            seg = (
                seg
                .faces(">Z" if bolt_half else "<Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.screw if bolt_half else self.nut, captiveNut=not bolt_half, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
                .moveTo(-self.seg_w + self.seg_h,0)
                .clearanceHole(fastener=self.screw if bolt_half else self.nut, captiveNut=not bolt_half, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
            )
        else:
            seg = (
                seg
                .faces(">Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.screw if bolt_half else self.nut, captiveNut=not bolt_half, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=outer_seg)
                .faces("<Z" if bolt_half else ">Z").workplane()
                .moveTo(-self.seg_w + self.seg_h,0)
                .clearanceHole(fastener=self.screw if bolt_half else self.nut, captiveNut=not bolt_half, baseAssembly=assembly if outer_seg and self.show_screws else None, counterSunk=True)
            )
            seg = (
                seg.rotate((0,0,0), (0,1,0), 180)
                .translate((0,0,self.seg_thick if bolt_half else -2*self.seg_thick-self.key_thick))
            )
            
        return seg

    def make_mid_spacer(self):
        return (
            Workplane("XY").cylinder(self.key_thick, 6/2)
            .faces("|Z").shell(-1)
            .translate((0,0,-self.key_thick/2))
        )
    def make(self):
        a = Assembly()
        #a.add(self.make_seg(a, True, True))
        a.add(self.make_seg(a, False, True))
        #a.add(self.make_seg(a, True, False))
        #a.add(self.make_seg(a, False, False))
        #a.add(self.make_mid_spacer())
        return a

if "show_object" in locals():
    FoldingSwiss(show_screws=1).display(show_object)
    #FoldingSwiss().display_split(show_object)
