import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pose_sequence_to_bedrock import convert


class PoseSequenceTest(unittest.TestCase):
    def setUp(self):
        self.rest={'bones':[{'name':'root','pivot':[0,0,0],'rotation':[0,0,0]},
            {'name':'child','parent':'root','pivot':[0,2,0],'rotation':[0,0,0],
             'cubes':[{'origin':[0,2,0],'size':[1,1,1],'uv':[0,0]}]}]}

    def test_parent_displacement_not_applied_twice(self):
        pose=copy.deepcopy(self.rest)
        for b in pose['bones']:b['pivot'][1]+=3
        pose['bones'][1]['cubes'][0]['origin'][1]+=3
        clip=convert(self.rest,[pose],'animation.test',loop=False)['animations']['animation.test']
        self.assertEqual(clip['bones']['root']['position']['0.0'],[0,3,0])
        self.assertNotIn('child',clip['bones'])

    def test_loop_closes_on_first_pose(self):
        a=copy.deepcopy(self.rest);b=copy.deepcopy(self.rest)
        b['bones'][1]['rotation']=[45,0,0]
        clip=convert(self.rest,[a,b],'animation.test',seconds=2)['animations']['animation.test']
        self.assertEqual(clip['bones']['child']['rotation'],{'0.0':[0,0,0],'1.0':[45,0,0],'2.0':[0,0,0]})

    def test_reject_changed_uv(self):
        pose=copy.deepcopy(self.rest);pose['bones'][1]['cubes'][0]['uv']=[4,4]
        with self.assertRaisesRegex(ValueError,'mesh/UV'):convert(self.rest,[pose],'animation.test')

    def test_reject_changed_hierarchy(self):
        pose=copy.deepcopy(self.rest);pose['bones'][1].pop('parent')
        with self.assertRaisesRegex(ValueError,'parent'):convert(self.rest,[pose],'animation.test')

    def test_reject_empty_and_nonfinite_timing(self):
        for poses,duration in [([],1),([self.rest],float('nan')),([self.rest],0)]:
            with self.assertRaises(ValueError):convert(self.rest,poses,'animation.test',seconds=duration)

if __name__=='__main__':unittest.main()
