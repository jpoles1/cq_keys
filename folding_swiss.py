from cadquery import *

from dataclasses import dataclass
import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

from cq_warehouse.fastener import SocketHeadCapScrew, HexNut
import cq_warehouse.extensions

@dataclass
class FoldingSwiss(StylishPart):
    seg_h: float = 28
    seg_w: float = 50
    seg_thick: float = 8
    hinge_thick = 3

    screw_offset = 5

    key_thick = 8

    max_fold_angle: float = 60

    show_screws: bool = True
    export: bool = True

    def calc_vars(self):
        self.screw = SocketHeadCapScrew(size="M4-0.7", length=20, fastener_type="iso4762", simple=True)
        self.nut = HexNut(size="M4-0.7", fastener_type="iso4032")
    
    def make_seg(self, assembly, outer_seg=True, bolt_half=True, keyring=False): 
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

        if keyring:
            seg = seg.union(
                Workplane("XY").moveTo(self.seg_w, 0).circle(2).extrude(self.seg_thick*0.8)
            )

        divot_size = 1
        cutout_size_mult = 1.2
        divot = (
            seg.faces("<Z[-2]").workplane()
            .moveTo(self.seg_h/4,0)
            .circle(divot_size).extrude(divot_size, combine=False)
            .faces("<Z").fillet(divot_size-0.001)
        )
        cut_divot = (
            seg.faces("<Z[-2]").workplane()
            .moveTo(self.seg_h/4,0)
            .circle(divot_size*cutout_size_mult).extrude(divot_size*cutout_size_mult, combine=False)
            .faces("<Z").fillet(divot_size*cutout_size_mult-0.001)
        )


        seg = seg.union(divot)
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180-(self.max_fold_angle-5)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180+(self.max_fold_angle-5)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))

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
        outer_bolt = self.make_seg(a, True, True)
        inner_bolt = self.make_seg(a, False, True)
        outer_nut = self.make_seg(a, True, False)
        inner_nut = self.make_seg(a, False, False)

        if self.export:
            parts_export = {"outer_bolt": outer_bolt, "inner_bolt": inner_bolt, "outer_nut": outer_nut, "inner_nut": inner_nut}
            {exporters.export(shape, './export/{fname}.stl'.format(fname=name)) for (name, shape) in parts_export.items()}


        a.add(outer_bolt)
        a.add(inner_bolt)
        a.add(outer_nut)
        a.add(inner_nut)
        a.add(self.make_mid_spacer())
        return a

if "show_object" in locals():
    FoldingSwiss(show_screws=1, export=0).display(show_object)
    #FoldingSwiss(show_screws=1).export().display(show_object)
    #FoldingSwiss().display_split(show_object)
