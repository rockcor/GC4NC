import datetime
import os
from copy import deepcopy

import scipy

from graphslim.condensation.gcond_base import GCondBase
from graphslim.dataset.utils import save_reduced
from graphslim.evaluation.utils import verbose_time_memory
from graphslim.models import *
from graphslim.models.gntk import GNTK
from graphslim.models.reparam_module import ReparamModule
from graphslim.sparsification import *
from graphslim.utils import *


class SFGC(GCondBase):
    def __init__(self, setting, data, args, **kwargs):
        super(SFGC, self).__init__(setting, data, args, **kwargs)

    @verbose_time_memory
    def reduce(self, data, verbose=True):
        args = self.args
        # =============stage 1 trajectory save==================#
        log_dir = './SFGC_Buffer/{}-{}'.format(args.dataset, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))

        if args.setting == 'ind':
            features = data.feat_train
            adj = data.adj_train
            labels = data.labels_train
        else:
            features = data.feat_full
            adj = data.adj_full
            labels = data.labels_full

        features, adj, label = to_tensor(features, adj, label=labels, device=self.device)
        device = args.device

        trajectories = []

        model_type = 'GCN'

        for it in range(200):

            model_class = eval(model_type)

            model = model_class(nfeat=features.shape[1], nhid=args.hidden, dropout=args.dropout,
                                nlayers=args.nlayers,
                                nclass=data.nclass, device=device).to(device)
            # print(model)

            model.initialize()

            model_parameters = list(model.parameters())

            optimizer_model = torch.optim.Adam(model_parameters, lr=args.lr, weight_decay=args.weight_decay)

            timestamps = []

            timestamps.append([p.detach().cpu() for p in model.parameters()])

            best_val_acc = best_test_acc = best_it = 0

            # lr_schedule = [args.teacher_epochs // 2 + 1]
            #
            # lr = args.lr
            for e in range(args.epochs):
                model.train()
                optimizer_model.zero_grad()
                _, output = model.forward(features, adj)
                if args.setting == 'ind':
                    loss_buffer = F.nll_loss(output, labels)
                else:
                    loss_buffer = F.nll_loss(output[data.idx_train], labels[data.idx_train])
                loss_buffer.backward()
                optimizer_model.step()

                # if e in lr_schedule and args.decay:
                #     lr = lr * args.decay_factor
                #     optimizer_model = torch.optim.Adam(model_parameters, lr=lr,
                #                                        weight_decay=args.wd_teacher)

                optimizer_model.zero_grad()

                if e % 10 == 0 and e > 1:
                    timestamps.append([p.detach().cpu() for p in model.parameters()])
                    # p_current = timestamps[-1]
                    # p_0 = timestamps[0]
                    # target_params = torch.cat([p_c.data.reshape(-1) for p_c in p_current], 0)
                    # starting_params = torch.cat([p0.data.reshape(-1) for p0 in p_0], 0)
                    # param_dist1 = torch.nn.functional.mse_loss(starting_params, target_params, reduction="sum")

            trajectories.append(timestamps)

            if len(trajectories) == args.traj_save_interval:
                n = 0
                while os.path.exists(os.path.join(log_dir, "replay_buffer_{}.pt".format(n))):
                    n += 1
                print("Saving {}".format(os.path.join(log_dir, "replay_buffer_{}.pt".format(n))))
                # torch.save(trajectories, os.path.join(log_dir, "replay_buffer_{}.pt".format(n)))
                trajectories = []
        # =============stage 2 coreset init==================#
        agent = KCenter(setting=args.setting, data=data, args=args)
        init_data = agent.reduce(data, verbose=args.verbose)
        # =============stage 3 trajectory alignment and GNTK evaluation==================#

        feat_init, adj_init, labels_init = to_tensor(init_data.feat_syn, init_data.adj_syn, init_data.labels_syn,
                                                     device=self.device)
        if args.setting == 'ind':
            features, adj, labels = to_tensor(data.feat_train, data.adj_train, data.labels_train, device=self.device)
        else:
            features, adj, labels = to_tensor(data.feat_full, data.adj_full, data.labels_full, device=self.device)
        adj_tensor_norm = normalize_adj_tensor(adj, sparse=True)
        self.feat_syn.data.copy_(feat_init)
        self.labels_syn = labels_init
        self.adj_syn_init = adj_init

        file_idx, expert_idx, expert_files = self.expert_load()

        syn_lr = torch.tensor(args.lr_student).to(self.device)

        if args.optim_lr == 1:
            syn_lr = syn_lr.detach().to(self.device).requires_grad_(True)
            optimizer_lr = torch.optim.Adam([syn_lr], lr=args.lr_lr)

        args.eval_type = 'GCN'
        model_eval_pool = self.get_eval_pool(args.eval_type, args.condense_model, args.eval_model)
        accs_all_exps = dict()  # record performances of all experiments

        best_ntk_score_eval = {m: 10 for m in model_eval_pool}
        best_ntk_score_eval_iter = {m: 0 for m in model_eval_pool}
        best_ntk_accs_eval = {m: 0 for m in model_eval_pool}
        best_ntk_accs_eval_iter = {m: 0 for m in model_eval_pool}

        # best_model_acc_eval = {m: 0 for m in model_eval_pool}
        # best_model_acc_eval_iter = {m: 0 for m in model_eval_pool}
        # best_model_std_eval = {m: 0 for m in model_eval_pool}
        #
        # best_model_acc_test = {m: 0 for m in model_eval_pool}
        # best_model_acc_test_iter = {m: 0 for m in model_eval_pool}
        # best_model_std_test = {m: 0 for m in model_eval_pool}

        best_loss = 1.0
        # best_loss_it = 0
        # adj_syn_norm_key = {'0': 0}

        for it in range(args.epochs):
            # logging.info(adj_syn_norm_key['0'])
            if args.dataset in ['ogbn-arxiv']:
                model = GCN(nfeat=data.feat_train.shape[1], nhid=args.student_hidden,
                            nclass=data.nclass, dropout=args.student_dropout, nlayers=args.student_nlayers,
                            device=self.device).to(self.device)
            else:
                if args.condense_model == 'SGC':
                    model = SGC(nfeat=data.feat_train.shape[1], nhid=args.student_hidden,
                                nclass=data.nclass, dropout=args.student_dropout,
                                nlayers=args.student_nlayers, with_bn=False,
                                device=self.device).to(self.device)
                elif args.condense_model == 'GCN':
                    model = GCN(nfeat=data.feat_train.shape[1], nhid=args.student_hidden,
                                nclass=data.nclass, dropout=args.student_dropout, nlayers=args.student_nlayers,
                                device=self.device).to(self.device)

            model = ReparamModule(model)

            model.train()

            num_params = sum([np.prod(p.size()) for p in (model.parameters())])

            if args.load_all:
                expert_trajectory = self.buffer[np.random.randint(0, len(self.buffer))]
            else:
                expert_trajectory = self.buffer[expert_idx]
                expert_idx += 1
                if expert_idx == len(self.buffer):
                    expert_idx = 0
                    file_idx += 1
                    if file_idx == len(expert_files):
                        file_idx = 0
                        random.shuffle(expert_files)
                    print("loading file {}".format(expert_files[file_idx]))
                    if args.max_files != 1:
                        del self.buffer
                        self.buffer = torch.load(expert_files[file_idx])
                    if args.max_experts is not None:
                        self.buffer = self.buffer[:args.max_experts]
                    random.shuffle(self.buffer)

            if args.rand_start == 1:
                if args.interval_buffer == 1:
                    start = np.linspace(0, args.start_epoch, num=args.start_epoch // 10 + 1)
                    start_epoch = int(np.random.choice(start, 1)[0])
                    start_epoch = start_epoch // 10
                else:
                    start_epoch = np.random.randint(0, args.start_epoch)
            elif args.rand_start == 0:
                if args.interval_buffer == 1:
                    start_epoch = args.start_epoch // 10
                else:
                    start_epoch = args.start_epoch

            starting_params = expert_trajectory[start_epoch]

            if args.interval_buffer == 1:
                target_params = expert_trajectory[start_epoch + args.expert_epochs // 10]
            else:
                target_params = expert_trajectory[start_epoch + args.expert_epochs]

            target_params = torch.cat([p.data.to(self.device).reshape(-1) for p in target_params], 0)

            student_params = [
                torch.cat([p.data.to(self.device).reshape(-1) for p in starting_params], 0).requires_grad_(True)]

            starting_params = torch.cat([p.data.to(self.device).reshape(-1) for p in starting_params], 0)

            param_loss_list = []
            param_dist_list = []

            if it == 0:
                feat_syn = self.feat_syn
                adj_syn_norm = normalize_adj_tensor(self.adj_syn_init, sparse=True)
                adj_syn_input = adj_syn_norm
            else:
                feat_syn = self.feat_syn
                adj_syn = torch.eye(feat_syn.shape[0]).to(self.device)
                adj_syn_cal_norm = normalize_adj_tensor(adj_syn, sparse=False)
                adj_syn_input = adj_syn_cal_norm
            for step in range(200):
                forward_params = student_params[-1]
                feat_out, output_syn = model.forward(feat_syn, adj_syn_input, flat_param=forward_params)
                loss_syn = F.nll_loss(output_syn, self.labels_syn)
                grad = torch.autograd.grad(loss_syn, student_params[-1], create_graph=True)[0]
                acc_syn = accuracy(output_syn, self.labels_syn)
                student_params.append(student_params[-1] - syn_lr * grad)
                # if step % 500 == 0:
                #     _, output_test = model.forward(features, adj_tensor_norm, flat_param=student_params[-1])
                # if args.setting == 'ind':
                #     acc_test = accuracy(output_test, labels)
                # else:
                #     acc_test = accuracy(output_test[data.idx_test], labels[data.idx_test])
                # print('loss = {:.4f},acc_syn = {:.4f},acc_test = {:.4f}'.format(loss_syn.item(),
                #                                                                 acc_syn.item(),
                #                                                                 acc_test.item()))

            param_loss = torch.tensor(0.0).to(self.device)
            param_dist = torch.tensor(0.0).to(self.device)

            param_loss += F.mse_loss(student_params[-1], target_params, reduction="sum")
            param_dist += F.mse_loss(starting_params, target_params, reduction="sum")
            param_loss_list.append(param_loss)
            param_dist_list.append(param_dist)

            param_loss /= num_params
            param_dist /= num_params

            param_loss /= param_dist

            grand_loss = param_loss
            # total_loss = grand_loss + ntk_loss
            total_loss = grand_loss
            self.optimizer_feat.zero_grad()

            if args.optim_lr == 1:
                optimizer_lr.zero_grad()

            # grand_loss.backward()
            total_loss.backward()
            # print(torch.min(self.feat_syn), torch.max(self.feat_syn), torch.min(self.feat_syn.grad), torch.max(self.feat_syn.grad))
            self.optimizer_feat.step()
            if torch.isnan(total_loss) or torch.isnan(grand_loss):
                break  # Break out of the loop if either is NaN
            if it % 1 == 0:
                print.info(
                    "Iteration {}: Total_Loss = {:.4f}, Grand_Loss={:.4f}, Start_Epoch= {}, Student_LR = {:6f}".format(
                        it,
                        total_loss.item(),
                        grand_loss.item(),
                        start_epoch,
                        syn_lr.item()))

            if it in args.checkpoints:
                for model_eval in model_eval_pool:
                    print('Evaluation: model_train = {}, model_eval = {}, iteration = {}'.format(args.condense_model,
                                                                                                 model_eval,
                                                                                                 it))
                    ntk_score_eval = []
                    ntk_accs_eval = []

                    ntk_score_eval_o, ntk_acc_test_o, ntk_feat_syn_save, ntk_adj_syn_save, ntk_label_syn_save = self.evaluate_synset_ntk()
                    ntk_score_eval.append(ntk_score_eval_o)
                    ntk_accs_eval.append(ntk_acc_test_o)

                    print(
                        'This is learned adj_syn INFO with {}-th iters: Shape: {}, Sum: {}, Avg_value: {}, Sparsity :{}'
                        .format(it, ntk_adj_syn_save.shape, ntk_adj_syn_save.sum(),
                                ntk_adj_syn_save.sum() / (ntk_adj_syn_save.shape[0] ** 2),
                                ntk_adj_syn_save.nonzero().shape[0] / (ntk_adj_syn_save.shape[0] ** 2)))

                    ntk_score_eval = np.array(ntk_score_eval)
                    ntk_accs_eval = np.array(ntk_accs_eval)

                    ntk_accs_eval_mean = np.mean(ntk_accs_eval)
                    # acc_test_std = np.std(accs_test)

                    ntk_score_eval_mean = np.mean(ntk_score_eval)
                    # score_test_std = np.std(score_test)

                    if ntk_score_eval_mean < best_ntk_score_eval[model_eval]:
                        best_ntk_score_eval[model_eval] = ntk_score_eval_mean
                        best_ntk_score_eval_iter[model_eval] = it
                        save_reduced(ntk_adj_syn_save, ntk_feat_syn_save, ntk_label_syn_save, args)

                    print('Evaluate ntk {}, score_mean = {:.4f}, acc_mean = {:.2f}'.format(model_eval,
                                                                                           ntk_score_eval_mean,
                                                                                           ntk_accs_eval_mean * 100.0))

            for _ in student_params:
                del _

        return data

    def expert_load(self):
        args = self.args
        expert_dir = args.buffer_path

        if args.load_all:
            buffer = []
            n = 0
            while os.path.exists(os.path.join(expert_dir, "replay_buffer_{}.pt".format(n))):
                buffer = buffer + torch.load(os.path.join(expert_dir, "replay_buffer_{}.pt".format(n)))
                n += 1
            if n == 0:
                raise AssertionError("No buffers detected at {}".format(expert_dir))

        else:
            expert_files = []
            n = 0
            while os.path.exists(os.path.join(expert_dir, "replay_buffer_{}.pt".format(n))):
                expert_files.append(os.path.join(expert_dir, "replay_buffer_{}.pt".format(n)))
                n += 1
            if n == 0:
                raise AssertionError("No buffers detected at {}".format(expert_dir))
            file_idx = 0
            expert_idx = 0
            random.shuffle(expert_files)
            if args.max_files is not None:
                expert_files = expert_files[:args.max_files]
            print("loading file {}".format(expert_files[file_idx]))
            buffer = torch.load(expert_files[file_idx])
            if args.max_experts is not None:
                buffer = buffer[:args.max_experts]
            random.shuffle(buffer)
            self.buffer = buffer

        return file_idx, expert_idx, expert_files

    def synset_save(self):
        args = self.args
        eval_labs = self.labels_syn
        with torch.no_grad():
            feat_save = self.feat_syn

        feat_syn_eval, label_syn_eval = deepcopy(feat_save.detach()), deepcopy(
            eval_labs.detach())  # avoid any unaware modification

        adj_syn_eval = torch.eye(feat_syn_eval.shape[0]).to(self.device)

        return feat_syn_eval, adj_syn_eval, label_syn_eval

    def evaluate_synset_ntk(self):
        args = self.args
        eval_labs = self.labels_syn
        data = self.data
        layers = 3
        gntk = GNTK(num_layers=layers, num_mlp_layers=2, jk=0, scale='degree')
        features_0, adj_0, labels_0 = data.feat_val, data.adj_val, data.labels_val
        num_class = max(labels_0) + 1

        feat_syn_eval, adj_syn_eval, labels_syn_eval = self.synset_save()
        feat_syn, adj_syn, labels_syn = np.array(feat_syn_eval.cpu()), np.array(adj_syn_eval.cpu()), np.array(
            labels_syn_eval.cpu())
        adj_syn = adj_syn + scipy.sparse.identity(adj_syn.shape[0])

        diag_syn = gntk.diag(feat_syn, adj_syn)

        labels_syn = one_hot_sfgc(labels_syn, num_class)

        _, sigma_syn_syn, ntk_syn_syn, dotsigma_syn_syn = calc(gntk, feat_syn, feat_syn, diag_syn, diag_syn,
                                                               adj_syn, adj_syn)
        if args.dataset == 'ogbn-arxiv':
            score_syn_ls = []
            acc_syn_ls = []
            for k in range(args.samp_iter):
                node_idx = data.retrieve_class_sampler_val(transductive=False, num_per_class=args.samp_num_per_class)
                re_adj_0 = adj_0[np.ix_(node_idx, node_idx)]
                re_feat_0 = features_0[node_idx, :]
                re_adj_0 = re_adj_0 + scipy.sparse.identity(re_adj_0.shape[0])
                re_labels_0 = one_hot(labels_0, num_class)[node_idx, :]
                diag_val = gntk.diag(re_feat_0, re_adj_0)
                _, sigma_val_syn, ntk_val_syn, dotsigma_val_syn = calc(gntk, re_feat_0, feat_syn, diag_val, diag_syn,
                                                                       re_adj_0,
                                                                       adj_syn)
                score_syn, acc_syn = loss_acc_fn_eval(data, ntk_syn_syn[-1], ntk_val_syn[-1], labels_syn, re_labels_0,
                                                      reg=args.ntk_reg)

                score_syn_ls.append(score_syn.item())
                acc_syn_ls.append(acc_syn.item())
                print(
                    'The graph ntk KRR score within the {}-th sampling in validation score = {:.4f}, acc = {:.2f}'.format(
                        k,
                        score_syn,
                        acc_syn * 100.))
            score_syn_np = np.array(score_syn_ls)
            acc_syn_np = np.array(acc_syn_ls)

            score_syn_mean = np.mean(score_syn_np)
            acc_syn_mean = np.mean(acc_syn_np)
            print('AVG KRR score = {:.4f}, acc = {:.2f}'.format(
                score_syn_mean,
                acc_syn_mean * 100.))

        else:
            adj_0 = adj_0 + scipy.sparse.identity(adj_0.shape[0])
            labels_0 = one_hot_sfgc(labels_0, num_class)
            diag_val = gntk.diag(features_0, adj_0)
            _, sigma_val_syn, ntk_val_syn, dotsigma_val_syn = calc(gntk, features_0, feat_syn, diag_val, diag_syn,
                                                                   adj_0,
                                                                   adj_syn)
            score_syn, acc_syn = loss_acc_fn_eval(data, ntk_syn_syn[-1], ntk_val_syn[-1], labels_syn, labels_0,
                                                  reg=args.ntk_reg)

            print(
                'The graph ntk KRR score within in validation score = {:.4f}, acc = {:.2f}'.format(
                    score_syn,
                    acc_syn * 100.))

            score_syn_mean = score_syn
            acc_syn_mean = acc_syn

        return score_syn_mean, acc_syn_mean, feat_syn_eval, adj_syn_eval, labels_syn_eval

    def get_eval_pool(self, eval_mode, model, model_eval):
        if eval_mode == 'M':  # multiple architectures
            model_eval_pool = [model, 'GAT', 'MLP', 'APPNP', 'GraphSage', 'Cheby', 'GCN']
        elif eval_mode == 'S':  # itself
            model_eval_pool = [model[:model.index('BN')]] if 'BN' in model else [model]
        else:
            model_eval_pool = [model_eval]
        return model_eval_pool
