from cadquery import *

from dataclasses import dataclass
import sys
sys.path.append("../cq_style")
from cq_style import StylishPart

from cq_warehouse.fastener import SocketHeadCapScrew, HexNut
import cq_warehouse.extensions

@dataclass
class FoldingSwiss(StylishPart):
    seg_w: float = 28 #Sets the segment dimension which corresponds to the length of your keys
    seg_l: float = 50 #Sets the segment dimension which corresponds to the width of your keys
    seg_thick: float = 6
    hinge_thick: float = 4
    key_thick: float = 7
    
    side_screw_offset: float = 7
    max_fold_angle: float = 60

    show_screws: bool = True
    export: bool = True

    def calc_vars(self):
        fastner_length = 16
        side_fastener_size = "M3-0.5"
        mid_fastener_size = "M3-0.5"
        self.side_screw = SocketHeadCapScrew(size=side_fastener_size, length=fastner_length, fastener_type="iso4762", simple=True)
        self.mid_screw = SocketHeadCapScrew(size=mid_fastener_size, length=fastner_length, fastener_type="iso4762", simple=True)
        self.side_nut = HexNut(size=side_fastener_size, fastener_type="iso4032")
        self.mid_nut = HexNut(size=mid_fastener_size, fastener_type="iso4032")
    
    def make_seg(self, assembly, outer=True, bolt_half=True, keyring=False): 
        #If inner_seg, this is the segment which is on the inside of the hinge. It is thinner as it does not need to accomodate the bolt head/nut
        hinge_cutout_thick = self.seg_thick - self.hinge_thick if outer else self.hinge_thick
        hinge_cutout = (
            Workplane("XZ")
            .moveTo(self.seg_w/2,0)
            .rect(self.seg_l, hinge_cutout_thick, centered=[0,0])
            .revolve(self.max_fold_angle * 2, (0,0), (0,1))
            .rotate((0,0,0), (0,0,1), -self.max_fold_angle)
            .translate((-self.seg_w/2, 0, 0))
            .copyWorkplane(Workplane("XY"))
            .circle(self.seg_w/2).extrude(hinge_cutout_thick)
        )

        seg = (
            Workplane("XY").moveTo(self.seg_w/2-self.seg_l/2).rect(self.seg_l, self.seg_w)
            .extrude(self.seg_thick)
            .edges("|Z").fillet(self.seg_w/2-0.05)
            .cut(hinge_cutout)
        )
        
        seg = seg.faces("|Z").fillet(0.5)

        if keyring:
            ring_ir = 3
            ring_or = ring_ir + 1.5
            arm_l = 4
            overlap_l = 2
            seg = seg.union(
                seg.faces(">Z").workplane(invert=1)
                .moveTo(-self.seg_l+self.seg_w/2-arm_l, 0)
                .rect(arm_l+overlap_l,2*ring_or, centered=[0,1])
                .extrude(self.seg_thick*0.6, combine=False)
                .moveTo(-self.seg_l+self.seg_w/2-arm_l, 0)
                .circle(ring_or)
                .extrude(self.seg_thick*0.6)
                .moveTo(-self.seg_l+self.seg_w/2-arm_l, 0)
                .circle(ring_ir).cutThruAll()
                .rotate((self.seg_w-self.seg_l,0,0), (self.seg_w-self.seg_l,0,1), 35)
                .faces("|Z").fillet(0.5)
            )


        divot_size = 1
        cutout_size_mult = 1.25
        divot = (
            seg.faces("<Z[-2]").workplane()
            .moveTo(self.seg_w/4,0)
            .circle(divot_size).extrude(divot_size, combine=False)
            .faces("<Z").fillet(divot_size-0.001)
        )
        cut_divot = (
            seg.faces("<Z[-2]").workplane()
            .moveTo(self.seg_w/4,0)
            .circle(divot_size*cutout_size_mult).extrude(divot_size*cutout_size_mult, combine=False)
            .faces("<Z").fillet(divot_size*cutout_size_mult-0.001)
        )


        seg = seg.union(divot)
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180-(self.max_fold_angle-10)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))
        seg = seg.cut(cut_divot.rotate((0,0,0), (0,0,1), 180+(self.max_fold_angle-10)).rotate((0,0,hinge_cutout_thick), (1,0,hinge_cutout_thick), 180))

        if not bolt_half:
            seg = seg.rotate((0,0,0), (1,0,0), 180).translate((0,0,-self.key_thick))
        if outer:
            seg = (
                seg
                .faces(">Z" if bolt_half else "<Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.mid_screw if bolt_half else self.mid_nut, captiveHex=not bolt_half, baseAssembly=assembly if outer and self.show_screws else None, counterSunk=outer)
                .moveTo(self.side_screw_offset+self.seg_w/2-self.seg_l,0)
                .clearanceHole(fastener=self.side_screw if bolt_half else self.side_nut, captiveHex=not bolt_half, baseAssembly=assembly if outer and self.show_screws else None, counterSunk=outer)
            )
        else:
            seg = (
                seg
                .faces(">Z").workplane().moveTo(0,0)
                .clearanceHole(fastener=self.mid_screw if bolt_half else self.mid_nut, captiveHex=not bolt_half, baseAssembly=assembly if outer and self.show_screws else None, counterSunk=outer)
                .faces("<Z" if bolt_half else ">Z").workplane()
                .moveTo(self.side_screw_offset+self.seg_w/2-self.seg_l ,0)
                .clearanceHole(fastener=self.side_screw if bolt_half else self.side_nut, captiveHex=not bolt_half, baseAssembly=assembly if outer and self.show_screws else None, counterSunk=True)
            )
            seg = (
                seg.rotate((0,0,0), (0,1,0), 180)
                .translate((0,0,self.seg_thick if bolt_half else -2*self.key_thick-self.seg_thick))
            )
        
        return seg

    def make_mid_spacer(self):
        
        spacer_thick = self.key_thick - 1
        spacer_ir = self.mid_screw.clearance_hole_diameters["Normal"] / 2 
        
        return (
            Workplane("XY").workplane(invert=1)
            .cylinder(spacer_thick, spacer_ir, centered=[1,1,0])
            .faces("|Z").shell(1)
            .translate((0,0,(spacer_thick-self.key_thick)/2))
        )

    def make(self):
        a = Assembly()
        outer_bolt = self.make_seg(a, outer=True, bolt_half=True, keyring=True)
        inner_bolt = self.make_seg(a, outer=False, bolt_half=True)
        outer_nut = self.make_seg(a, outer=True, bolt_half=False)
        inner_nut = self.make_seg(a, outer=False, bolt_half=False)
        mid_spacer = self.make_mid_spacer()

        if self.export:
            parts_export = {"outer_bolt": outer_bolt, "inner_bolt": inner_bolt, "outer_nut": outer_nut, "inner_nut": inner_nut, "mid_spacer": mid_spacer}
            {exporters.export(shape, './export/{fname}.stl'.format(fname=name)) for (name, shape) in parts_export.items()}


        a.add(outer_bolt)
        a.add(inner_bolt)
        a.add(outer_nut)
        a.add(inner_nut)
        a.add(mid_spacer)
        return a

if "show_object" in locals():
    FoldingSwiss(show_screws=1, export=1).display(show_object)
    #FoldingSwiss().display_split(show_object)
